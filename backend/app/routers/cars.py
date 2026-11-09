# backend/app/routers/cars.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from app.db.session import get_db
from app.models.car import CarCatalog, UserCar
from app.services.charging_calc import calculate_charge_estimate

router = APIRouter(prefix="/api/v1", tags=["Cars & Charging"])

class CarCatalogOut(BaseModel):
    id: int
    make: str
    model: str
    battery_capacity_kwh: float
    max_ac_power_kw: float
    max_dc_power_kw: float
    connector_type: str

    class Config:
        from_attributes = True

class UserCarCreate(BaseModel):
    catalog_car_id: Optional[int] = None
    make: Optional[str] = None
    model: Optional[str] = None
    battery_capacity_kwh: Optional[float] = None
    max_ac_power_kw: Optional[float] = 11.0
    max_dc_power_kw: Optional[float] = 80.0
    connector_type: Optional[str] = "GB/T"
    set_active: bool = True

class EstimateRequest(BaseModel):
    user_car_id: int
    station_id: int
    current_soc: int = Field(ge=0, le=99)
    target_soc: int = Field(ge=1, le=100)

class EstimateResponse(BaseModel):
    energy_kwh: float
    duration_minutes: int
    total_cost_rub: float
    effective_power_kw: float


@router.get("/cars/catalog", response_model=List[CarCatalogOut])
def get_catalog(db: Session = Depends(get_db)):
    return db.query(CarCatalog).order_by(CarCatalog.make, CarCatalog.model).all()


@router.post("/users/me/cars")
def add_user_car(payload: UserCarCreate, db: Session = Depends(get_db)):
    # Тестовая заглушка user_id = 1 (замените на get_current_user)
    current_user_id = 1 

    if payload.catalog_car_id:
        catalog_item = db.query(CarCatalog).filter(CarCatalog.id == payload.catalog_car_id).first()
        if not catalog_item:
            raise HTTPException(status_code=404, detail="Модель авто не найдена в каталоге")
        
        new_car = UserCar(
            user_id=current_user_id,
            catalog_car_id=catalog_item.id,
            make=catalog_item.make,
            model=catalog_item.model,
            battery_capacity_kwh=catalog_item.battery_capacity_kwh,
            max_ac_power_kw=catalog_item.max_ac_power_kw,
            max_dc_power_kw=catalog_item.max_dc_power_kw,
            connector_type=catalog_item.connector_type,
            is_custom=False,
            is_active=payload.set_active
        )
    else:
        if not (payload.make and payload.model and payload.battery_capacity_kwh):
            raise HTTPException(status_code=400, detail="Для кастомного авто требуются марка, модель и емкость батареи")
        
        new_car = UserCar(
            user_id=current_user_id,
            catalog_car_id=None,
            make=payload.make,
            model=payload.model,
            battery_capacity_kwh=payload.battery_capacity_kwh,
            max_ac_power_kw=payload.max_ac_power_kw,
            max_dc_power_kw=payload.max_dc_power_kw,
            connector_type=payload.connector_type,
            is_custom=True,
            is_active=payload.set_active
        )

    if payload.set_active:
        db.query(UserCar).filter(UserCar.user_id == current_user_id).update({"is_active": False})

    db.add(new_car)
    db.commit()
    db.refresh(new_car)
    return new_car


@router.post("/charging/estimate", response_model=EstimateResponse)
def estimate_charging(req: EstimateRequest, db: Session = Depends(get_db)):
    car = db.query(UserCar).filter(UserCar.id == req.user_car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")

    # Пример параметров станции (в реальности получаем из таблицы Station по req.station_id)
    station_power_kw = 60.0
    station_type = "DC"
    price_per_kwh = 18.50

    result = calculate_charge_estimate(
        battery_capacity_kwh=car.battery_capacity_kwh,
        current_soc=req.current_soc,
        target_soc=req.target_soc,
        station_power_kw=station_power_kw,
        station_type=station_type,
        car_max_ac_kw=car.max_ac_power_kw,
        car_max_dc_kw=car.max_dc_power_kw,
        price_per_kwh=price_per_kwh
    )

    return EstimateResponse(
        energy_kwh=result.energy_needed_kwh,
        duration_minutes=result.duration_minutes,
        total_cost_rub=result.total_cost_rub,
        effective_power_kw=result.effective_power_kw
    )