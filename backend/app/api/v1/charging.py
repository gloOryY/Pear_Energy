from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_driver
from app.db.session import get_db
from app.models import User
from app.models.charging import ChargingSession
from app.models.enums import LimitType, SessionStatus, StopReason
from app.models.station import Station
from app.schemas.charging import ExtendLimitIn, QuoteIn, QuoteOut, SessionOut, StartSessionIn
from app.services.charging_service import compute_quote, create_session, request_stop, validate_can_start
from app.utils.ids import uid

router = APIRouter(prefix="/charging-sessions", tags=["charging"])


@router.post("/quote", response_model=QuoteOut)
async def quote(data: QuoteIn, db: AsyncSession = Depends(get_db), user: User = Depends(require_driver)):
    station = await db.get(Station, data.station_id)
    if not station:
        raise HTTPException(404, "Не найдено")
    q = compute_quote(station, data.limit_type, data.limit_value)
    return QuoteOut(station_id=data.station_id, limit_type=data.limit_type, limit_value=data.limit_value,
                     **{k: v for k, v in q.items() if k in QuoteOut.model_fields})


@router.post("/start", response_model=SessionOut, status_code=201)
async def start_session(data: StartSessionIn, user: User = Depends(require_driver),
                         db: AsyncSession = Depends(get_db)):
    station = await db.get(Station, data.station_id)
    if not station or not station.is_active:
        raise HTTPException(404, "Не найдено")
    try:
        await validate_can_start(db, str(user.id), station)
        session = await create_session(
            db, user_id=str(user.id), station=station, limit_type=data.limit_type,
            limit_value=data.limit_value, tariff=station.tariff_per_kwh,
            min_launch_amount=station.min_launch_amount)
        await db.commit()
        await db.refresh(session)
        return session
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.post("/{sid}/stop", response_model=SessionOut)
async def stop_session(sid: str, user: User = Depends(require_driver), db: AsyncSession = Depends(get_db)):
    session = await db.get(ChargingSession, sid)
    if not session or session.user_id != user.id:
        raise HTTPException(404, "Не найдено")
    if session.status not in (SessionStatus.preparing, SessionStatus.charging, SessionStatus.suspended_ev):
        raise HTTPException(409, "Сессию нельзя остановить в текущем статусе")
    await request_stop(db, session, StopReason.user)
    await db.commit()
    await db.refresh(session)
    return session


@router.post("/{sid}/extend", response_model=SessionOut)
async def extend_limit(sid: str, data: ExtendLimitIn, user: User = Depends(require_driver),
                        db: AsyncSession = Depends(get_db)):
    session = await db.get(ChargingSession, sid)
    if not session or session.user_id != user.id:
        raise HTTPException(404, "Не найдено")
    if session.status != SessionStatus.charging:
        raise HTTPException(409, "Сессия не активна")
    add = data.add_rub if session.selected_limit_type == LimitType.rub else data.add_kwh
    if add is None:
        add = data.add_rub or data.add_kwh
    session.selected_limit_value = session.selected_limit_value + (add or 0)
    from app.models.hardware import StationCommand
    db.add(StationCommand(
        id=uid(), station_id=session.station_id, type="update_limits",
        payload={"session_id": session.id, "limit_type": session.selected_limit_type.value,
                 "limit_value": str(session.selected_limit_value)},
        idempotency_key=f"limits:{session.id}:{int(session.selected_limit_value * 1000)}",
    ))
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/{sid}", response_model=SessionOut)
async def get_session(sid: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    session = await db.get(ChargingSession, sid)
    if not session or (session.user_id != user.id and user.role.value != "admin"):
        raise HTTPException(404, "Не найдено")
    return session


@router.get("/me", response_model=list[SessionOut])
async def my_sessions(user: User = Depends(require_driver), db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(ChargingSession).where(ChargingSession.user_id == user.id)
                              .order_by(ChargingSession.created_at.desc()).limit(100))).scalars().all()
