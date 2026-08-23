import math
from datetime import datetime, timezone

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_station_device, require_driver
from app.db.session import get_db
from app.models import Location, Review, StationPhoto, User
from app.models.booking import Booking
from app.models.enums import BookingStatus, ModerationStatus, StationStatus
from app.models.hardware import StationCommand
from app.models.station import Station
from app.schemas.booking import BookingIn, BookingOut
from app.schemas.station import AvailabilityOut, ReviewOut, StationDetail, StationShort
from app.services.telemetry_service import heartbeat, ingest_telemetry
from app.utils.ids import uid

router = APIRouter(tags=["stations"])

POWER_BUCKETS: dict[str, tuple[float, float]] = {
    "p3.7": (0, 3.7), "p7.4": (3.71, 7.4), "p11": (7.41, 11), "p22": (11.01, 22),
}
STATUS_GROUPS: dict[str, list[StationStatus]] = {
    "free": [StationStatus.available],
    "busy": [StationStatus.vehicle_connected, StationStatus.awaiting_payment,
             StationStatus.preparing, StationStatus.suspended_ev, StationStatus.finishing],
    "charging": [StationStatus.charging],
    "offline": [StationStatus.offline, StationStatus.unavailable],
    "faulted": [StationStatus.faulted, StationStatus.emergency_stop],
}


async def load_detail(db: AsyncSession, st: Station, loc: Location | None) -> StationDetail:
    photos = (await db.execute(select(StationPhoto.url).where(
        StationPhoto.station_id == st.id, StationPhoto.status == ModerationStatus.approved.value
    ))).scalars().all()
    d = StationDetail.model_validate(st)
    if loc:
        d.location_name, d.address, d.city = loc.name, loc.address, loc.city
        d.description, d.amenities, d.schedule = loc.description, loc.amenities, loc.schedule
        d.venue_types = loc.venue_types
    d.photos = list(loc.photo_urls) + list(photos) if loc else list(photos)
    return d


@router.get("/stations", response_model=list[StationShort])
async def list_stations(
    q: str | None = Query(None),
    status_group: list[str] = Query([], alias="status"),
    power: list[str] = Query([]),
    tariff_max: float | None = Query(None, gt=0),
    open24: bool = False,
    booking: bool = False,
    venue: list[str] = Query([]),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Station, Location).join(Location, Station.location_id == Location.id).where(
        Station.is_active == True)  # noqa: E712
    if q:
        like = f"%{q.strip().lower()}%"
        stmt = stmt.where(or_(Location.city.ilike(like), Location.address.ilike(like),
                              Location.name.ilike(like), Station.name.ilike(like)))
    if status_group:
        statuses = [s for g in status_group for s in STATUS_GROUPS.get(g, [])]
        if statuses:
            stmt = stmt.where(Station.status.in_(statuses))
    if power:
        conds = [Station.max_power_kw.between(lo, hi) for key in power
                 for lo, hi in [POWER_BUCKETS.get(key, (None, None))] if lo is not None]
        if conds:
            stmt = stmt.where(or_(*conds))
    if tariff_max:
        stmt = stmt.where(Station.tariff_per_kwh <= tariff_max)
    if booking:
        stmt = stmt.where(Station.supports_booking == True)  # noqa: E712
    if venue:
        stmt = stmt.where(Location.venue_types.op("&&")(venue))

    rows = (await db.execute(stmt.order_by(Station.name).limit(500))).all()
    out = []
    for st, loc in rows:
        item = StationShort.model_validate(st)
        item.city, item.address = loc.city, loc.address
        item.photo = (loc.photo_urls or [None])[0]
        out.append(item)
    return out


@router.get("/stations/nearby", response_model=list[StationShort])
async def nearby(lat: float, lon: float, radius_km: float = 15, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(Station, Location).join(Location, Station.location_id == Location.id)
        .where(Station.is_active == True))).all()  # noqa: E712
    out = []
    for st, loc in rows:
        dist = _haversine(lat, lon, float(st.latitude), float(st.longitude))
        if dist <= radius_km:
            item = StationShort.model_validate(st)
            item.city, item.address = loc.city, loc.address
            item.photo = (loc.photo_urls or [None])[0]
            out.append(item)
    out.sort(key=lambda s: _haversine(lat, lon, float(s.latitude), float(s.longitude)))
    return out


def _haversine(a_lat, a_lon, b_lat, b_lon) -> float:
    r = 6371
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp, dl = math.radians(b_lat - a_lat), math.radians(b_lon - a_lon)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


@router.get("/stations/{public_id}", response_model=StationDetail)
async def station_detail(public_id: str, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(Station, Location).join(
        Location, Station.location_id == Location.id).where(Station.public_id == public_id))).first()
    if not row:
        raise HTTPException(404, "Не найдено")
    return await load_detail(db, row[0], row[1])


@router.get("/stations/{public_id}/reviews", response_model=list[ReviewOut])
async def station_reviews(public_id: str, db: AsyncSession = Depends(get_db)):
    st = (await db.execute(select(Station).where(Station.public_id == public_id))).scalar_one_or_none()
    if not st:
        raise HTTPException(404, "Не найдено")
    rows = (await db.execute(select(Review, User).join(User, Review.user_id == User.id).where(
        Review.station_id == st.id, Review.status == ModerationStatus.approved.value
    ).order_by(Review.created_at.desc()).limit(50))).all()
    return [ReviewOut(id=r.id, rating=r.rating, text=r.text, created_at=r.created_at, author=u.full_name)
            for r, u in rows]


@router.get("/stations/{public_id}/availability", response_model=AvailabilityOut)
async def station_availability(public_id: str, db: AsyncSession = Depends(get_db)):
    st = (await db.execute(select(Station).where(Station.public_id == public_id))).scalar_one_or_none()
    if not st:
        raise HTTPException(404, "Не найдено")
    now = datetime.now(timezone.utc)
    bks = (await db.execute(select(Booking).where(
        Booking.station_id == st.id, Booking.status == BookingStatus.active, Booking.ends_at >= now
    ))).scalars().all()
    return AvailabilityOut(status=st.status, bookings=[
        {"starts_at": b.starts_at.isoformat(), "ends_at": b.ends_at.isoformat()} for b in bks])


@router.post("/stations/{public_id}/booking", response_model=BookingOut, status_code=201)
async def create_booking(public_id: str, data: BookingIn, user: User = Depends(require_driver),
                          db: AsyncSession = Depends(get_db)):
    st = (await db.execute(select(Station).where(Station.public_id == public_id))).scalar_one_or_none()
    if not st or not st.is_active:
        raise HTTPException(404, "Не найдено")
    if not st.supports_booking:
        raise HTTPException(400, "Станция не поддерживает бронирование")
    now = datetime.now(timezone.utc)
    if data.starts_at < now:
        raise HTTPException(422, "Начало в прошлом")
    overlap = (await db.execute(select(Booking).where(
        Booking.station_id == st.id, Booking.status == BookingStatus.active,
        Booking.starts_at < data.ends_at, Booking.ends_at > data.starts_at
    ))).scalar_one_or_none()
    if overlap:
        raise HTTPException(409, "Слот занят")
    b = Booking(id=uid(), user_id=user.id, station_id=st.id, starts_at=data.starts_at,
                ends_at=data.ends_at, amount=Decimal(st.booking_amount))
    db.add(b)
    await db.commit()
    await db.refresh(b)
    return b


@router.get("/stations/{public_id}/photos", response_model=list[str])
async def station_photos(public_id: str, db: AsyncSession = Depends(get_db)):
    st = (await db.execute(select(Station).where(Station.public_id == public_id))).scalar_one_or_none()
    if not st:
        raise HTTPException(404, "Не найдено")
    urls = (await db.execute(select(StationPhoto.url).where(
        StationPhoto.station_id == st.id, StationPhoto.status == ModerationStatus.approved.value))).scalars().all()
    return list(urls)


@router.post("/stations/{public_id}/telemetry")
async def post_telemetry(public_id: str, data: dict, station=Depends(get_station_device),
                          db: AsyncSession = Depends(get_db)):
    out = await ingest_telemetry(db, station, data)
    await db.commit()
    return out


@router.post("/stations/{public_id}/heartbeat")
async def post_heartbeat(public_id: str, station=Depends(get_station_device), db: AsyncSession = Depends(get_db)):
    await heartbeat(db, station)
    await db.commit()
    return {"ok": True, "server_time": datetime.now(timezone.utc).isoformat()}


@router.get("/stations/{public_id}/commands/next")
async def next_command(public_id: str, station=Depends(get_station_device), db: AsyncSession = Depends(get_db)):
    cmd = (await db.execute(
        select(StationCommand).where(StationCommand.station_id == station.id, StationCommand.status == "pending")
        .order_by(StationCommand.created_at.asc()).limit(1))).scalar_one_or_none()
    if not cmd:
        return {"command": None}
    cmd.status = "sent"
    await db.commit()
    return {"command": {"id": cmd.id, "type": cmd.type, "payload": cmd.payload}}


@router.post("/stations/{public_id}/command-result")
async def command_result(public_id: str, data: dict, station=Depends(get_station_device),
                          db: AsyncSession = Depends(get_db)):
    from app.services.charging_service import apply_command_result
    cmd = await db.get(StationCommand, data.get("command_id"))
    if not cmd or cmd.station_id != station.id:
        raise HTTPException(404, "Не найдено")
    await apply_command_result(db, cmd, ok=bool(data.get("ok")), result=data.get("result") or {})
    await db.commit()
    return {"ok": True}
