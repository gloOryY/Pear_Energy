import csv
import io
from datetime import timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_operator
from app.db.base import utcnow
from app.db.session import get_db
from app.models import Location, StationPhoto, SupportTicket, User
from app.models.charging import ChargingSession
from app.models.enums import ModerationStatus, SessionStatus, StationStatus
from app.models.hardware import StationTelemetry
from app.models.payment import Payment
from app.models.station import Station
from app.schemas.station import StationDetail
from app.utils.ids import uid

router = APIRouter(prefix="/operator", tags=["operator"], dependencies=[Depends(require_operator)])


def owner_locations_stmt(user: User):
    stmt = select(Location)
    if user.role.value != "admin":
        stmt = stmt.where(Location.owner_id == user.id)
    return stmt


@router.get("/stations", response_model=list[StationDetail])
async def my_stations(user: User = Depends(require_operator), db: AsyncSession = Depends(get_db)):
    locs = (await db.execute(owner_locations_stmt(user))).scalars().all()
    out = []
    for loc in locs:
        sts = (await db.execute(select(Station).where(Station.location_id == loc.id))).scalars().all()
        for st in sts:
            from app.api.v1.stations import load_details
            out.append(await load_details(db, st, loc))
    return out


@router.get("/stats")
async def stats(
    period: str = Query("day", pattern="day|week|month"),
    user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    delta = {"day": timedelta(days=1), "week": timedelta(days=7), "month": timedelta(days=30)}.get(period, timedelta(days=30))
    since = utcnow() - delta
    loc_ids = (await db.execute(
        select(Location.id).where(Location.owner_id == user.id if user.role.value != "admin" else True)
    )).scalars().all()
    if not loc_ids:
        return {"revenue": 0, "platform_fee": 0, "sessions": 0, "avg_kwh": 0, "uptime_percent": 100}
    st_ids = (await db.execute(select(Station.id).where(Station.location_id.in_(loc_ids)))).scalars().all()
    rows = (await db.execute(
        select(ChargingSession).where(
            ChargingSession.station_id.in_(st_ids),
            ChargingSession.status == SessionStatus.completed,
            ChargingSession.end_at >= since,
        )
    )).scalars().all()
    revenue = sum(s.total_amount for s in rows) or Decimal(0)
    loc0 = (await db.execute(select(Location).where(Location.id.in_(loc_ids)))).scalars().first()
    share = Decimal(str(loc0.owner_share_percent)) if loc0 else Decimal("90.0")
    sessions_n = len(rows)
    avg_kwh = round(sum(float(s.energy_kwh) for s in rows) / sessions_n, 2) if sessions_n else 0
    hb = (await db.execute(
        select(func.count(StationTelemetry.id)).where(
            StationTelemetry.station_id.in_(st_ids),
            StationTelemetry.timestamp >= since,
            StationTelemetry.error_code.is_(None),
        )
    )).scalar() or 0
    expected = max(1, int(delta.total_seconds() / 30) * len(st_ids))
    return {
        "revenue": float(revenue * share / 100),
        "platform_fee": float(revenue * (100 - share) / 100),
        "sessions": sessions_n,
        "avg_kwh": avg_kwh,
        "uptime_percent": round(min(100.0, hb / expected * 100), 1),
    }


@router.get("/faults")
async def faults_journal(user: User = Depends(require_operator), db: AsyncSession = Depends(get_db)):
    stmt = (
        select(StationTelemetry, Station)
        .join(Station, StationTelemetry.station_id == Station.id)
        .where(StationTelemetry.error_code.isnot(None))
        .order_by(StationTelemetry.timestamp.desc())
        .limit(100)
    )
    if user.role.value != "admin":
        stmt = stmt.join(Location, Station.location_id == Location.id).where(Location.owner_id == user.id)
    rows = (await db.execute(stmt)).all()
    return [{"station": st.public_id, "at": t.timestamp, "code": t.error_code, "evse": t.evse_state, "temp": float(t.temperature_c or 0)} for t, st in rows]


@router.patch("/stations/{public_id}")
async def update_station(public_id: str, patch: dict, user: User = Depends(require_operator), db: AsyncSession = Depends(get_db)):
    st = (await db.execute(select(Station).where(Station.public_id == public_id))).scalar_one_or_none()
    if not st:
        raise HTTPException(404, "Станция не найдена")
    if user.role.value != "admin":
        loc = await db.get(Location, st.location_id)
        if not loc or loc.owner_id != user.id:
            raise HTTPException(403, "Недостаточно прав")
    for field in ["tariff_per_kwh", "supports_booking", "is_active", "booking_amount", "min_launch_amount", "parking_info"]:
        if field in patch:
            setattr(st, field, patch[field])
    await db.commit()
    return {"ok": True}


@router.patch("/locations/{loc_id}")
async def update_location(loc_id: str, patch: dict, user: User = Depends(require_operator), db: AsyncSession = Depends(get_db)):
    loc = await db.get(Location, loc_id)
    if not loc or (user.role.value != "admin" and loc.owner_id != user.id):
        raise HTTPException(404, "Локация не найдена")
    for field in ["schedule", "description", "amenities", "photo_urls", "owner_share_percent"]:
        if field in patch:
            setattr(loc, field, patch[field])
    await db.commit()
    return {"ok": True}


@router.post("/stations", status_code=201)
async def add_station(body: dict, user: User = Depends(require_operator), db: AsyncSession = Depends(get_db)):
    loc = Location(
        id=uid(),
        owner_id=user.id,
        name=body["location_name"],
        address=body["address"],
        city=body["city"],
        latitude=body["latitude"],
        longitude=body["longitude"],
        amenities=body.get("amenities", []),
        schedule={"always_open": True},
        venue_types=body.get("venue_types", []),
        photo_urls=body.get("photo_urls", []),
    )
    db.add(loc)
    await db.flush()
    seq = (await db.execute(select(func.count(Station.id)))).scalar() + 1
    prefix = {"Москва": "MSK", "Санкт-Петербург": "SPB", "Казань": "KZN", "Нижний Новгород": "NN", "Сочи": "SOCHI"}.get(body["city"], "M4" if "-4" in body["address"] else "MO")
    st = Station(
        id=uid(),
        location_id=loc.id,
        public_id=f"CP-{prefix}-{seq:03d}",
        name=body["station_name"],
        serial_number=f"SN{uid()[:12].upper()}",
        device_token=f"devtok{uid()[:24]}",
        max_power_kw=body["max_power_kw"],
        max_current_a=body.get("max_current_a", 32),
        tariff_per_kwh=body["tariff_per_kwh"],
        latitude=body["latitude"],
        longitude=body["longitude"],
        status=StationStatus.offline,
    )
    db.add(st)
    await db.commit()
    return {"public_id": st.public_id, "device_token": st.device_token, "note": "Сохраните device_token для прошивки ESP32"}


@router.post("/stations/{public_id}/photos")
async def add_photo(public_id: str, url: str, user: User = Depends(require_operator), db: AsyncSession = Depends(get_db)):
    st = (await db.execute(select(Station).where(Station.public_id == public_id))).scalar_one_or_none()
    if not st:
        raise HTTPException(404, "Станция не найдена")
    db.add(StationPhoto(id=uid(), station_id=st.id, url=url, uploaded_by=user.id))
    await db.commit()
    return {"ok": True, "moderation": "pending"}


@router.get("/payments")
async def payments_view(period: str = "month", user: User = Depends(require_operator), db: AsyncSession = Depends(get_db)):
    delta = {"day": timedelta(days=1), "week": timedelta(days=7), "month": timedelta(days=30)}.get(period, timedelta(days=30))
    loc_ids = (await db.execute(select(Location.id).where(Location.owner_id == user.id if user.role.value != "admin" else True))).scalars().all()
    st_ids = (await db.execute(select(Station.id).where(Station.location_id.in_(loc_ids or [])))).scalars().all()
    pays = (await db.execute(
        select(Payment, ChargingSession)
        .join(ChargingSession, Payment.session_id == ChargingSession.id, isouter=True)
        .where(ChargingSession.station_id.in_(st_ids or []), Payment.created_at >= utcnow() - delta)
        .order_by(Payment.created_at.desc())
        .limit(200)
    )).all()
    return [{"id": p.id, "amount": float(p.amount), "status": p.status.value, "method": p.method.value, "paid_at": p.paid_at, "session": s.id if s else None} for p, s in pays]


@router.get("/export.csv")
async def export_csv(period: str = "month", user: User = Depends(require_operator), db: AsyncSession = Depends(get_db)):
    pays = await payments_view(period, user, db)  # type: ignore[arg-type]
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(["payment_id", "amount_rub", "status", "method", "paid_at", "session_id"])
    for p in pays:
        writer.writerow([p["id"], p["amount"], p["status"], p["method"], p["paid_at"] or "", p["session"] or ""])
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=report.csv"})
