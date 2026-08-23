import logging
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import utcnow
from app.models import Notification
from app.models.charging import ChargingSession
from app.models.enums import (CommandType, LimitType, PaymentStatus, SessionStatus,
                               StationStatus, StopReason)
from app.models.hardware import StationCommand
from app.models.payment import Receipt
from app.models.station import Connector, Station
from app.utils.audit import audit
from app.utils.ids import uid
from app.services.payment_service import money
from app.ws.eventbus import publish

log = logging.getLogger("charging")

ACTIVE_STATUSES = {SessionStatus.awaiting_payment, SessionStatus.preparing,
                   SessionStatus.charging, SessionStatus.suspended_ev, SessionStatus.finishing}

REASON_LABELS = {
    StopReason.user: "остановлено пользователем",
    StopReason.limit_reached: "достигнут выбранный лимит",
    StopReason.vehicle: "автомобиль прекратил запрос зарядки",
    StopReason.fault: "неисправность оборудования",
    StopReason.connection_lost: "потеря связи со станцией",
    StopReason.emergency: "аварийная остановка",
}


def compute_quote(station: Station, limit_type: LimitType, value: Decimal) -> dict:
    tariff = Decimal(station.tariff_per_kwh)
    power = float(station.max_power_kw)
    eff = 0.92

    est_kwh = est_min = est_amount = None
    if limit_type == LimitType.kwh:
        est_kwh = value
        est_amount = money(value * tariff)
        est_min = int(float(value) / (power * eff) * 60) if power else None
    elif limit_type == LimitType.rub:
        est_amount = money(value)
        est_kwh = (value / tariff).quantize(Decimal("0.01")) if tariff else None
        if est_kwh is not None and power:
            est_min = int(float(est_kwh) / (power * eff) * 60)
    elif limit_type == LimitType.minutes:
        est_min = int(value)
        hours = float(value) / 60
        est_kwh = Decimal(str(round(power * eff * hours, 2)))
        est_amount = money(est_kwh * tariff)
    # until_stop: всё неизвестно заранее

    return {
        "estimated_kwh": est_kwh, "estimated_minutes": est_min,
        "estimated_amount": est_amount,
        "tariff_per_kwh": tariff,
        "min_launch_amount": Decimal(station.min_launch_amount),
    }


async def validate_can_start(db: AsyncSession, user_id: str, station: Station) -> None:
    if not station.is_active:
        raise ValueError("Станция отключена оператором")
    if station.status not in (StationStatus.available, StationStatus.vehicle_connected,
                               StationStatus.awaiting_payment):
        raise ValueError(f"Станция сейчас недоступна ({station.status.value})")
    dup = (await db.execute(
        select(ChargingSession).where(
            ChargingSession.user_id == user_id,
            ChargingSession.status.in_(ACTIVE_STATUSES),
        ))).scalars().first()
    if dup:
        raise ValueError("У вас уже есть активная сессия зарядки")


async def create_session(db: AsyncSession, *, user_id: str, station: Station,
                          limit_type: LimitType, limit_value: Decimal,
                          tariff: Decimal, min_launch_amount: Decimal) -> ChargingSession:
    if limit_type == LimitType.rub and limit_value < min_launch_amount:
        raise ValueError(f"Минимальная сумма запуска — {min_launch_amount} ₽")

    session = ChargingSession(
        id=uid(), user_id=user_id, station_id=station.id,
        status=SessionStatus.awaiting_payment,
        tariff_per_kwh=tariff,
        selected_limit_type=limit_type,
        selected_limit_value=limit_value,
    )
    db.add(session)
    await db.flush()
    if station.status == StationStatus.available:
        station.status = StationStatus.awaiting_payment
    await audit(db, "session.created", actor_id=user_id, entity_type="session", entity_id=session.id)
    return session


async def create_start_command(db: AsyncSession, session: ChargingSession) -> StationCommand:
    """Идемпотентная команда старта. Создаётся только после payment=succeeded."""
    cmd = StationCommand(
        id=uid(), station_id=session.station_id, type=CommandType.start,
        payload={
            "session_id": session.id,
            "limit_type": session.selected_limit_type.value,
            "limit_value": str(session.selected_limit_value),
            "tariff_per_kwh": str(session.tariff_per_kwh),
            "max_charge_minutes": 12 * 60,  # страховка на стороне железа
        },
        idempotency_key=f"start:{session.id}",
        status="pending",
    )
    db.add(cmd)
    await audit(db, "command.start_queued", entity_type="session", entity_id=session.id)
    return cmd


async def confirm_after_payment(db: AsyncSession, payment) -> None:
    """Вызывается из payment_service.process_succeeded."""
    session = await db.get(ChargingSession, payment.session_id)
    if session is None or session.status != SessionStatus.awaiting_payment:
        return
    session.payment_id = payment.id
    session.status = SessionStatus.preparing
    await create_start_command(db, session)
    await db.flush()

    station = await db.get(Station, session.station_id)
    if station and station.status in (StationStatus.awaiting_payment, StationStatus.available):
        station.status = StationStatus.preparing

    db.add(Notification(id=uid(), user_id=session.user_id,
                         title="Оплата прошла — зарапуска зарядка",
                         body=f"Станция {station.public_id if station else ''}. Сессия {session.id[:8]}..."))
    await publish([f"user:{session.user_id}", f"station:{station.public_id if station else ''}"],
                  {"type": "session.updated", "session_id": session.id,
                   "status": SessionStatus.preparing.value})


async def apply_command_result(db: AsyncSession, cmd: StationCommand, *,
                                ok: bool, result: dict) -> None:
    cmd.status = "completed" if ok else "failed"
    from app.db.base import utcnow
    cmd.completed_at = utcnow()

    if cmd.type == CommandType.start:
        session = await _session_by_cmd_payload(db, cmd)
        if session is None:
            return
        station = await db.get(Station, session.station_id)
        if ok:
            session.status = SessionStatus.charging
            session.start_at = utcnow()
            ms = result.get("meter_start_kwh")
            session.meter_start_kwh = Decimal(str(ms)) if ms is not None else Decimal("0")
            if station:
                station.status = StationStatus.charging
            await _bind_connector(db, session, busy=True)
            await audit(db, "command.start_ok", entity_type="session", entity_id=session.id)
        else:
            session.status = SessionStatus.failed
            session.stop_reason = StopReason.fault
            if station:
                station.status = StationStatus.faulted
            await _auto_refund_pending(db, session)
        await _notify_session(db, session)

    elif cmd.type == CommandType.stop:
        session = await _session_by_cmd_payload(db, cmd)
        if session is None:
            return
        if ok:
            reason = result.get("reason", cmd.payload.get("reason", StopReason.user.value))
            meter_end = result.get("meter_end_kwh")
            await finalize_session(db, session,
                                    meter_end_kwh=Decimal(str(meter_end)) if meter_end is not None else None,
                                    reason=StopReason(reason))
        else:
            await audit(db, "command.stop_failed", entity_type="session",
                        entity_id=cmd.payload.get("session_id"))

    elif cmd.type in (CommandType.lock, CommandType.unlock):
        station = await db.get(Station, cmd.station_id)
        if station and ok:
            station.status = StationStatus.unavailable if cmd.type == CommandType.lock \
                else StationStatus.available

    await db.flush()


async def request_stop(db: AsyncSession, session: ChargingSession, reason: StopReason) -> None:
    cmd = StationCommand(
        id=uid(), station_id=session.station_id, type=CommandType.stop,
        payload={"session_id": session.id, "reason": reason.value},
        idempotency_key=f"stop:{session.id}:{utcnow().timestamp():.0f}",
        status="pending",
    )
    db.add(cmd)
    session.status = SessionStatus.finishing
    from app.core.config import settings
    if settings.STATION_MODE == "mock":
        from app.gateways.mock_gateway import MockStationGateway
        gw = MockStationGateway()
        await gw.send_stop_command(session.station_id, session.id, reason.value)
    await audit(db, "command.stop_requested", actor_id=session.user_id,
                entity_type="session", entity_id=session.id, meta={"reason": reason.value})


async def finalize_session(db: AsyncSession, session: ChargingSession, *,
                            meter_end_kwh: Decimal | None, reason: StopReason) -> None:
    if session.status in (SessionStatus.completed, SessionStatus.cancelled, SessionStatus.failed):
        return

    if meter_end_kwh is None:
        from app.models.hardware import StationTelemetry
        last = (await db.execute(
            select(StationTelemetry).where(StationTelemetry.station_id == session.station_id)
            .order_by(StationTelemetry.timestamp.desc()).limit(1))).scalar_one_or_none()
        meter_end_kwh = Decimal(str(last.energy_total_kwh)) if last and last.energy_total_kwh is not None \
            else (session.meter_start_kwh or Decimal(0)) + session.energy_kwh

    session.meter_end_kwh = meter_end_kwh
    if session.meter_start_kwh is not None:
        session.energy_kwh = max(Decimal(0), meter_end_kwh - session.meter_start_kwh).quantize(Decimal("0.001"))
    session.total_amount = money(session.energy_kwh * session.tariff_per_kwh)
    session.end_at = utcnow()
    session.status = SessionStatus.completed
    session.stop_reason = reason

    station = await db.get(Station, session.station_id)
    if station:
        station.status = StationStatus.available
    await _bind_connector(db, session, busy=False)

    receipt = Receipt(
        id=uid(),
        payment_id=session.payment_id or "no-payment",
        session_id=session.id,
        number=f"RCP-{session.id[:10].upper()}",
        data={
            "start_at": str(session.start_at), "end_at": str(session.end_at),
            "energy_kwh": str(session.energy_kwh), "tariff": str(session.tariff_per_kwh),
            "total": str(session.total_amount), "stop_reason": reason.value,
            "transaction": session.payment_id, "station": station.public_id if station else None,
        },
    )
    db.add(receipt)
    db.add(Notification(id=uid(), user_id=session.user_id, title="Зарядка завершена",
                         body=f"{session.energy_kwh} кВт·ч · {session.total_amount} ₽ · причина: {REASON_LABELS.get(reason, reason.value)}"))
    await audit(db, "session.completed", entity_type="session", entity_id=session.id,
                meta={"energy": str(session.energy_kwh), "total": str(session.total_amount),
                      "reason": reason.value})
    if station:
        await publish([f"user:{session.user_id}", f"station:{station.public_id}"],
                      {"type": "session.completed", "session_id": session.id,
                       "total": str(session.total_amount), "energy": str(session.energy_kwh)})


async def cancel_stale_awaiting_payment(db: AsyncSession, minutes: int = 30) -> None:
    deadline = utcnow() - timedelta(minutes=minutes)
    rows = (await db.execute(
        select(ChargingSession).where(
            ChargingSession.status == SessionStatus.awaiting_payment,
            ChargingSession.created_at < deadline))).scalars().all()
    for s in rows:
        s.status = SessionStatus.cancelled
        st = await db.get(Station, s.station_id)
        if st and st.status == StationStatus.awaiting_payment:
            st.status = StationStatus.available
        if s.payment_id:
            from app.models.payment import Payment
            pay = await db.get(Payment, s.payment_id)
            if pay and pay.status == PaymentStatus.pending:
                pay.status = PaymentStatus.cancelled


# ── внутренние помощники ────────────────────────────────────────────

async def _session_by_cmd_payload(db: AsyncSession, cmd: StationCommand) -> ChargingSession | None:
    sid = cmd.payload.get("session_id")
    return await db.get(ChargingSession, sid) if sid else None


async def _bind_connector(db: AsyncSession, session: ChargingSession, *, busy: bool) -> None:
    if not session.connector_id:
        conn = (await db.execute(select(Connector).where(Connector.station_id == session.station_id))).scalars().first()
        session.connector_id = conn.id if conn else None
    if session.connector_id:
        conn = await db.get(Connector, session.connector_id)
        if conn:
            conn.status = "busy" if busy else "available"
            conn.current_session_id = session.id if busy else None


async def _notify_session(db: AsyncSession, session: ChargingSession) -> None:
    station = await db.get(Station, session.station_id)
    await publish([f"user:{session.user_id}", f"station:{station.public_id if station else ''}"],
                  {"type": "session.updated", "session_id": session.id, "status": session.status.value})


async def _auto_refund_pending(db: AsyncSession, session: ChargingSession) -> None:
    """Если старт не удался — возвращаем средства за незапущенную зарядку."""
    from app.models.payment import Payment, Refund
    if not session.payment_id:
        return
    pay = await db.get(Payment, session.payment_id)
    if pay and pay.status == PaymentStatus.succeeded:
        db.add(Refund(id=uid(), payment_id=pay.id, amount=pay.amount,
                       reason="Старт зарядки не состоялся"))
        pay.status = PaymentStatus.refunded
