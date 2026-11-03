import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.station import Station, Connector
from app.schemas.station import StationCreate, StationUpdate, StationResponse

router = APIRouter(prefix="/stations", tags=["Stations"])

UPLOAD_DIR = "static/uploads/stations"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("", response_model=StationResponse, status_code=status.HTTP_201_CREATED)
async def create_station(payload: StationCreate, db: AsyncSession = Depends(get_db)):
    station_data = payload.model_dump(exclude={"connectors"})
    station_id = str(uuid.uuid4())
    
    station = Station(id=station_id, **station_data)
    db.add(station)

    # Создание списка разъемов станции
    for idx, conn_data in enumerate(payload.connectors, start=1):
        connector = Connector(
            id=str(uuid.uuid4()),
            station_id=station_id,
            connector_number=conn_data.connector_number or idx,
            type=conn_data.type,
            max_power_kw=conn_data.max_power_kw,
            status=conn_data.status
        )
        db.add(connector)

    await db.commit()
    
    stmt = select(Station).where(Station.id == station_id).options(selectinload(Station.connectors))
    res = await db.execute(stmt)
    return res.scalar_one()


@router.get("", response_model=List[StationResponse])
async def list_stations(db: AsyncSession = Depends(get_db)):
    stmt = select(Station).options(selectinload(Station.connectors))
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/{station_id}", response_model=StationResponse)
async def get_station(station_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Station).where(Station.id == station_id).options(selectinload(Station.connectors))
    res = await db.execute(stmt)
    station = res.scalar_one_or_none()
    if not station:
        raise HTTPException(status_code=404, detail="Станция не найдена")
    return station


@router.patch("/{station_id}", response_model=StationResponse)
async def update_station(station_id: str, payload: StationUpdate, db: AsyncSession = Depends(get_db)):
    stmt = select(Station).where(Station.id == station_id).options(selectinload(Station.connectors))
    res = await db.execute(stmt)
    station = res.scalar_one_or_none()
    if not station:
        raise HTTPException(status_code=404, detail="Станция не найдена")

    update_data = payload.model_dump(exclude_unset=True)
    connectors_data = update_data.pop("connectors", None)

    for key, value in update_data.items():
        setattr(station, key, value)

    # Если передан обновленный список разъемов — перезаписываем их
    if connectors_data is not None:
        station.connectors.clear()
        for idx, c_dict in enumerate(connectors_data, start=1):
            station.connectors.append(
                Connector(
                    id=str(uuid.uuid4()),
                    station_id=station_id,
                    connector_number=c_dict.get("connector_number", idx),
                    type=c_dict["type"],
                    max_power_kw=c_dict["max_power_kw"],
                    status=c_dict.get("status", "available")
                )
            )

    await db.commit()
    await db.refresh(station)
    return station


@router.post("/{station_id}/photo")
async def upload_station_photo(
    station_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Station).where(Station.id == station_id)
    res = await db.execute(stmt)
    station = res.scalar_one_or_none()
    if not station:
        raise HTTPException(status_code=404, detail="Станция не найдена")

    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{station_id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)

    station.image_url = f"/static/uploads/stations/{filename}"
    await db.commit()
    return {"image_url": station.image_url}