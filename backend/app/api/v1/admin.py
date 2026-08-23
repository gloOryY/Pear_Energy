from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.db.session import get_db
from app.models import AuditLog, Location, Review, Setting, StationPhoto, User
from app.models.charging import ChargingSession
from app.models.enums import ModerationStatus, StationStatus
from app.models.hardware import StationCommand
from app.models.payment import Payment, Refund
from app.models.station import Station
from app.utils.ids import uid

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/users")
async def users(q: str = None, role: str = None, db: AsyncSession = Depends(get_db)):
    stmt = select(User).order_by(User.created_at.desc()).limit(200)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(User.email.ilike(like), User.full_name.ilike(like), User.phone.ilike(like)))
    if role:
        stmt = stmt.where(User.role == role)
    rows = (await db.execute(stmt)).scalars().all()
    return [{"id": u.id, "email": u.email, "phone": u.phone, "full_name": u.full_name, "role": u.role.value, "is_active": u.is_active} for u in rows]


@router.patch("/users/{user_id}")
async def patch_user(user_id: str, patch: dict, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    u = await db.get(User, user_id)
    if not u:
        raise HTTPException(404, "Пользователь не найден")
    if "is_active" in patch:
        u.is_active = bool(patch["is_active"])
    if "role" in patch and patch["role"] in ["driver", "operator", "admin"]:
        u.role = patch["role"]
    await db.commit()
    return {"ok": True}


@router.get("/stations")
async def stations(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Station, Location).join(Location, Station.location_id == Location.id))).all()
    return [{"public_id": st.public_id, "name": st.name, "city": loc.city, "owner_email": (await db.get(User, loc.owner_id)).email, "status": st.status.value, "tariff": float(st.tariff_per_kwh), "is_active": st.is_active} for st, loc in rows]


@router.post("/stations/{public_id}/lock")
async def lock_station(public_id: str, lock: bool = True, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    st = (await db.execute(select(Station).where(Station.public_id == public_id))).scalar_one_or_none()
    if not st:
        raise HTTPException(404, "Станция не найдена")
    cmd_type = "lock" if lock else "unlock"
    db.add(StationCommand(id=uid(), station_id=st.id, type=cmd_type, payload={}, idempotency_key=f"{cmd_type}_{st.public_id}"))
    st.status = StationStatus.unavailable if lock else StationStatus.available
    await db.commit()
    return {"ok": True, "command": cmd_type}


@router.get("/commands")
async def commands_history(station_public_id: str = None, db: AsyncSession = Depends(get_db)):
    stmt = select(StationCommand, Station).join(Station, StationCommand.station_id == Station.id).order_by(StationCommand.created_at.desc()).limit(200)
    if station_public_id:
        stmt = stmt.where(Station.public_id == station_public_id)
    rows = (await db.execute(stmt)).all()
    return [{"id": c.id, "station": st.public_id, "type": c.type, "status": c.status, "payload": c.payload, "created_at": c.created_at, "completed_at": c.completed_at} for c, st in rows]


@router.get("/payments")
async def payments(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Payment).order_by(Payment.created_at.desc()).limit(200))).scalars().all()
    return [{"id": p.id, "user": p.user_id, "amount": float(p.amount), "status": p.status.value, "method": p.method.value, "provider": p.provider, "paid_at": p.paid_at} for p in rows]


@router.post("/payments/{payment_id}/refund")
async def refund_payment(payment_id: str, amount: float = None, reason: str = "", db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    p = await db.get(Payment, payment_id)
    if not p or p.status.value != "succeeded":
        raise HTTPException(409, "Платёж не найден или не успешен")
    amt = amount or float(p.amount)
    db.add(Refund(id=uid(), payment_id=p.id, amount=amt, reason=reason))
    p.status = "refunded"
    await db.commit()
    return {"ok": True}


@router.get("/sessions")
async def sessions(limit: int = Query(100, le=500), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(ChargingSession).order_by(ChargingSession.created_at.desc()).limit(limit))).scalars().all()
    return [{"id": s.id, "user": s.user_id, "status": s.status.value, "energy": float(s.energy_kwh), "total": float(s.total_amount), "stop_reason": s.stop_reason.value if s.stop_reason else None} for s in rows]


@router.get("/audit")
async def audit_log(action: str = None, db: AsyncSession = Depends(get_db)):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(300)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    rows = (await db.execute(stmt)).scalars().all()
    return [{"id": a.id, "actor": a.actor_id, "action": a.action, "entity": a.entity_type, "entity_id": a.entity_id, "meta": a.meta, "at": a.created_at} for a in rows]


@router.get("/equipment-errors")
async def equipment_errors(db: AsyncSession = Depends(get_db)):
    from app.models.hardware import StationTelemetry
    rows = (await db.execute(
        select(StationTelemetry, Station)
        .join(Station, StationTelemetry.station_id == Station.id)
        .where(StationTelemetry.error_code.isnot(None))
        .order_by(StationTelemetry.timestamp.desc())
        .limit(100)
    )).all()
    return [{"station": st.public_id, "at": t.timestamp, "code": t.error_code, "evse": t.evse_state} for t, st in rows]


@router.get("/moderation/photos")
async def photos_moderation(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(StationPhoto).where(StationPhoto.status == ModerationStatus.pending))).scalars().all()
    return [{"id": p.id, "url": p.url, "station_id": p.station_id} for p in rows]


@router.patch("/moderation/photos/{photo_id}")
async def moderate_photo(photo_id: str, approve: bool, db: AsyncSession = Depends(get_db)):
    p = await db.get(StationPhoto, photo_id)
    if not p:
        raise HTTPException(404, "Фото не найдено")
    p.status = ModerationStatus.approved.value if approve else ModerationStatus.rejected.value
    await db.commit()
    return {"ok": True}


@router.get("/moderation/reviews")
async def reviews_moderation(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Review).where(Review.status == ModerationStatus.pending))).scalars().all()
    return [{"id": r.id, "rating": r.rating, "text": r.text, "station_id": r.station_id} for r in rows]


@router.patch("/moderation/reviews/{review_id}")
async def moderate_review(review_id: str, approve: bool, db: AsyncSession = Depends(get_db)):
    r = await db.get(Review, review_id)
    if not r:
        raise HTTPException(404, "Отзыв не найден")
    r.status = ModerationStatus.approved.value if approve else ModerationStatus.rejected.value
    await db.commit()
    return {"ok": True}


@router.get("/commissions")
async def commissions(db: AsyncSession = Depends(get_db)):
    plat = await db.get(Setting, "platform_commission_percent")
    rows = (await db.execute(select(Location))).scalars().all()
    return {
        "platform_commission_percent": float(plat.value) if plat else 10.0,
        "locations": [{"id": l.id, "name": l.name, "owner_share_percent": l.owner_share_percent} for l in rows],
    }


@router.put("/commissions")
async def set_commission(patch: dict, db: AsyncSession = Depends(get_db)):
    if "platform_commission_percent" in patch:
        s = await db.get(Setting, "platform_commission_percent")
        if not s:
            s = Setting(key="platform_commission_percent", value=str(patch["platform_commission_percent"]))
            db.add(s)
        else:
            s.value = str(patch["platform_commission_percent"])
    if "location_id" in patch and "owner_share_percent" in patch:
        loc = await db.get(Location, patch["location_id"])
        if loc:
            loc.owner_share_percent = float(patch["owner_share_percent"])
    await db.commit()
    return {"ok": True}
