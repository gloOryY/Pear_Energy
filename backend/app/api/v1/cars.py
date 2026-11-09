from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.car import CarCatalog, UserCar
from app.models.station import Station
from app.models.user import User
from app.services.charging_calc import calculate_charge_estimate

router = APIRouter(tags=["Cars & Charging"])


class CarCatalogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    make: str
    model: str
    battery_capacity_kwh: float
    max_ac_power_kw: float
    max_dc_power_kw: float
    connector_type: str


class UserCarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    catalog_car_id: Optional[int] = None
    make: str
    model: str
    battery_capacity_kwh: float
    max_ac_power_kw: float
    max_dc_power_kw: float
    connector_type: str
    is_active: bool
    is_custom: bool
    created_at: Optional[datetime] = None


class UserCarCreate(BaseModel):
    catalog_car_id: Optional[int] = None
    make: Optional[str] = None
    model: Optional[str] = None
    battery_capacity_kwh: Optional[float] = None
    max_ac_power_kw: Optional[float] = 11.0
    max_dc_power_kw: Optional[float] = 120.0
    connector_type: Optional[str] = "GB/T"
    set_active: bool = True


class EstimateRequest(BaseModel):
    user_car_id: Optional[int] = None
    battery_capacity_kwh: Optional[float] = None
    car_max_ac_kw: Optional[float] = 11.0
    car_max_dc_kw: Optional[float] = 120.0
    station_id: Optional[str] = None
    station_power_kw: Optional[float] = None
    station_type: Optional[str] = None
    price_per_kwh: Optional[float] = None
    price_per_minute: Optional[float] = None
    price_start: Optional[float] = None
    current_soc: int = Field(default=20, ge=0, le=99)
    target_soc: int = Field(default=80, ge=1, le=100)


class EstimateResponse(BaseModel):
    energy_kwh: float
    duration_minutes: int
    total_cost_rub: float
    effective_power_kw: float


@router.get("/cars/catalog", response_model=List[CarCatalogOut])
async def get_catalog(
    make: Optional[str] = Query(None, description="Фильтр по марке"),
    q: Optional[str] = Query(None, description="Поисковый запрос"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CarCatalog).order_by(CarCatalog.make, CarCatalog.model)
    if make:
        stmt = stmt.where(CarCatalog.make.ilike(f"%{make}%"))
    if q:
        q_term = f"%{q}%"
        stmt = stmt.where((CarCatalog.make.ilike(q_term)) | (CarCatalog.model.ilike(q_term)))
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/cars/catalog/makes", response_model=List[str])
async def get_catalog_makes(db: AsyncSession = Depends(get_db)):
    stmt = select(CarCatalog.make).distinct().order_by(CarCatalog.make)
    res = await db.execute(stmt)
    return [r[0] for r in res.all()]


@router.get("/users/me/cars", response_model=List[UserCarOut])
async def get_my_cars(
    user: User = Depends(get_current_user),


@router.post("/users/me/cars", response_model=UserCarOut, status_code=status.HTTP_201_CREATED)
async def add_my_car(
    payload: UserCarCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.catalog_car_id:
        catalog_item = await db.get(CarCatalog, payload.catalog_car_id)
        if not catalog_item:
            raise HTTPException(status_code=404, detail="Модель авто не найдена в каталоге")

        new_car = UserCar(
            user_id=user.id,
            catalog_car_id=catalog_item.id,
            make=catalog_item.make,
            model=catalog_item.model,
            battery_capacity_kwh=catalog_item.battery_capacity_kwh,
            max_ac_power_kw=catalog_item.max_ac_power_kw,
            max_dc_power_kw=catalog_item.max_dc_power_kw,
            connector_type=catalog_item.connector_type,
            is_custom=False,
            is_active=payload.set_active,
        )
    else:
        if not (payload.make and payload.model and payload.battery_capacity_kwh):
            raise HTTPException(
                status_code=400,
                detail="Для кастомного авто требуются марка, модель и емкость батареи",
            )

        new_car = UserCar(
            user_id=user.id,
            catalog_car_id=None,
            make=payload.make.strip(),
            model=payload.model.strip(),
            battery_capacity_kwh=float(payload.battery_capacity_kwh),
            max_ac_power_kw=float(payload.max_ac_power_kw or 11.0),
            max_dc_power_kw=float(payload.max_dc_power_kw or 120.0),
            connector_type=payload.connector_type or "GB/T",
            is_custom=True,
            is_active=payload.set_active,
        )

    existing_count = (
        await db.execute(select(UserCar).where(UserCar.user_id == user.id))
    ).scalars().all()

    if payload.set_active or len(existing_count) == 0:
        new_car.is_active = True
        await db.execute(
            update(UserCar).where(UserCar.user_id == user.id).values(is_active=False)
        )

    db.add(new_car)
    await db.commit()
    await db.refresh(new_car)
    return new_car


@router.put("/users/me/cars/{car_id}/active", response_model=UserCarOut)
async def set_active_car(
    car_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    car = await db.get(UserCar, car_id)
    if not car or car.user_id != user.id:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")

    await db.execute(
        update(UserCar).where(UserCar.user_id == user.id).values(is_active=False)
    )
    car.is_active = True
    await db.commit()
    await db.refresh(car)
    return car


@router.delete("/users/me/cars/{car_id}")
async def delete_my_car(
    car_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    car = await db.get(UserCar, car_id)
    if not car or car.user_id != user.id:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")

    was_active = car.is_active
    await db.delete(car)
    await db.commit()

    if was_active:
        remaining = (
            await db.execute(
                select(UserCar).where(UserCar.user_id == user.id).order_by(UserCar.id.desc())
            )
        ).scalars().first()
        if remaining:
            remaining.is_active = True
            await db.commit()

    return {"ok": True, "message": "Автомобиль удален"}


@router.post("/charging/estimate", response_model=EstimateResponse)
async def estimate_charging(
    req: EstimateRequest,
    db: AsyncSession = Depends(get_db),
):
    battery_kwh = req.battery_capacity_kwh or 75.0
    car_ac = req.car_max_ac_kw or 11.0
    car_dc = req.car_max_dc_kw or 120.0

    if req.user_car_id:
        car = await db.get(UserCar, req.user_car_id)
        if car:
            battery_kwh = car.battery_capacity_kwh
            car_ac = car.max_ac_power_kw
            car_dc = car.max_dc_power_kw

    station_power = req.station_power_kw or 22.0
    station_type = req.station_type or "AC"
    price_kwh = req.price_per_kwh or 0.0
    price_min = req.price_per_minute or 0.0
    price_start = req.price_start or 0.0

    if req.station_id:
        station = await db.get(Station, req.station_id)
        if station:
            station_power = float(station.max_power_kw or 22.0)
            price_kwh = float(station.tariff_per_kwh or 0.0)
            price_min = float(station.tariff_per_minute or 0.0)
            price_start = float(station.tariff_start or 0.0)

            ctype = str(station.connector_type.value if hasattr(station.connector_type, "value") else station.connector_type).lower()
            if any(dc_name in ctype for dc_name in ["dc", "ccs", "chademo"]):
                station_type = "DC"
            elif station_power > 22.0:
                station_type = "DC"
            else:
                station_type = "AC"

    result = calculate_charge_estimate(
        battery_capacity_kwh=battery_kwh,
        current_soc=req.current_soc,
        target_soc=req.target_soc,
        station_power_kw=station_power,
        station_type=station_type,
        car_max_ac_kw=car_ac,
        car_max_dc_kw=car_dc,
        price_per_kwh=price_kwh,
        price_per_minute=price_min,
        price_start=price_start,
    )

    return EstimateResponse(
        energy_kwh=result.energy_needed_kwh,
        duration_minutes=result.duration_minutes,
        total_cost_rub=result.total_cost_rub,
        effective_power_kw=result.effective_power_kw,
    )

    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(UserCar)
        .where(UserCar.user_id == user.id)
        .order_by(UserCar.is_active.desc(), UserCar.id.desc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()
