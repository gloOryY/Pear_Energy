"""Фоновые проверки надёжности:
1. Время выбранного лимита вышло → stop(limit_reached).
2. Станция не отвечает > 5 минут во время зарядки → stop(connection_lost) и offline.
3. Зависшие awaiting_payment сессии (>30 мин) → отмена."""
import asyncio
import logging
from datetime import timedelta

from sqlalchemy import select

from app.db.base import utcnow
from app.db.session import SessionLocal
from app.models.charging import ChargingSession
from app.models.enums import SessionStatus, StationStatus, StopReason
from app.models.station import Station
from app.services.charging_service import cancel_stale_awaiting_payment, request_stop

log = logging.getLogger("watchdog")
INTERVAL_SEC = 30


async def run_watchdog() -> None:
    while True:
        try:
            async with SessionLocal() as db:
                now = utcnow()

                charging = (await db.execute(
                    select(ChargingSession).where(ChargingSession.status == SessionStatus.charging)
                )).scalars().all()
                for s in charging:
                    if s.selected_limit_type.value == "minutes" and s.start_at:
                        if now - s.start_at > timedelta(minutes=float(s.selected_limit_value)):
                            await request_stop(db, s, StopReason.limit_reached)
                    station = await db.get(Station, s.station_id)
                    if station and station.last_seen_at and now - station.last_seen_at > timedelta(minutes=5):
                        await request_stop(db, s, StopReason.connection_lost)
                        station.status = StationStatus.offline

                stations = (await db.execute(
                    select(Station).where(Station.is_active == True,  # noqa: E712
                                           Station.status != StationStatus.unavailable))).scalars().all()
                for st in stations:
                    if st.last_seen_at and now - st.last_seen_at > timedelta(minutes=10) \
                            and st.status not in (StationStatus.offline, StationStatus.faulted,
                                                   StationStatus.unavailable):
                        st.status = StationStatus.offline

                await cancel_stale_awaiting_payment(db)
                await db.commit()
        except Exception:
            log.exception("watchdog tick failed")
        await asyncio.sleep(INTERVAL_SEC)
