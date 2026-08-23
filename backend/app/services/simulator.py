"""MockStationGateway: генерирует рост энергии и телеметрию, соблюдает лимиты,
останавливается по stop-команде и завершает сессию через charging_service."""
import asyncio
import contextlib
import logging
import time
from decimal import Decimal

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.charging import ChargingSession
from app.models.enums import LimitType, StopReason
from app.models.station import Station
from app.services.telemetry_service import ingest_telemetry

log = logging.getLogger("simulator")
TICK_SEC = 2.0


class SessionSimulator:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.stop_reason: str | None = None
        self.stop_event = asyncio.Event()
        self.task = asyncio.create_task(self._bootstrap())

    def request_stop(self, reason: str) -> None:
        self.stop_reason = reason
        self.stop_event.set()

    async def _bootstrap(self) -> None:
        with contextlib.suppress(Exception):
            await _run_session(self)


class SimulatorManager:
    def __init__(self) -> None:
        self.active: dict[str, SessionSimulator] = {}

    def launch(self, session_id: str) -> None:
        self.active[session_id] = SessionSimulator(session_id)

    def request_stop(self, session_id: str, reason: str) -> None:
        sim = self.active.get(session_id)
        if sim:
            sim.request_stop(reason)

    def finish(self, session_id: str) -> None:
        self.active.pop(session_id, None)


simulator_manager = SimulatorManager()


async def _run_session(sim: SessionSimulator) -> None:
    """Основной цикл мок-зарядки."""
    async with SessionLocal() as db:
        session = await db.get(ChargingSession, sim.session_id)
        if session is None:
            return
        station = await db.get(Station, session.station_id)

    phase_voltage = 230.0 if float(station.max_power_kw) <= 7.4 else 400.0
    max_power = float(station.max_power_kw)
    max_current = float(station.max_current_a)
    efficiency = 0.93

    meter = float(session.meter_start_kwh or 0)
    started = time.monotonic()
    limit_type = session.selected_limit_type
    limit_val = Decimal(session.selected_limit_value)

    while not sim.stop_event.is_set():
        await asyncio.sleep(TICK_SEC)
        elapsed_h = (time.monotonic() - started) / 3600
        power = round(min(max_power, max_current * phase_voltage / 1000) *
                      (0.85 + 0.15 * min(elapsed_h * 60, 1)), 3)
        current = round(power * 1000 / phase_voltage, 2)
        dt_h = TICK_SEC / 3600
        meter += power * dt_h * efficiency
        energy = round(meter - float(session.meter_start_kwh or 0), 3)

        telemetry = {
            "voltage_v": phase_voltage, "current_a": current, "power_kw": power,
            "energy_total_kwh": round(meter, 3), "temperature_c": 31.0 + elapsed_h,
            "evse_state": "charging", "error_code": None,
        }
        async with SessionLocal() as db2:
            st = await db2.get(Station, station.id)
            await ingest_telemetry(db2, st, telemetry)
            sess = await db2.get(ChargingSession, sim.session_id)

            eta = None
            if limit_type == LimitType.kwh:
                remaining = float(limit_val) - energy
                eta = max(0, int(remaining / max(power * efficiency, 0.01) * 60))
                if energy >= float(limit_val):
                    sim.request_stop(StopReason.limit_reached.value)
            elif limit_type == LimitType.rub:
                spent = energy * float(sess.tariff_per_kwh)
                eta = max(0, int((float(limit_val) - spent) /
                                  max(power * efficiency * float(sess.tariff_per_kwh), 0.01) * 60))
                if spent >= float(limit_val):
                    sim.request_stop(StopReason.limit_reached.value)
            elif limit_type == LimitType.minutes:
                mins = elapsed_h * 60
                eta = max(0, int(float(limit_val) - mins))
                if mins >= float(limit_val):
                    sim.request_stop(StopReason.limit_reached.value)
            else:  # until_stop
                eta = None
                if elapsed_h > 8:  # предохранитель 8 часов
                    sim.request_stop(StopReason.vehicle.value)

            from app.ws.eventbus import publish
            await publish([f"user:{sess.user_id}", f"station:{st.public_id}"],
                          {"type": "telemetry", "session_id": sess.id,
                           "power_kw": power, "current_a": current,
                           "voltage_v": phase_voltage, "energy_kwh": energy,
                           "total_amount": str(sess.total_amount),
                           "evse_state": "charging", "eta_minutes": eta})
            await db2.commit()

    async with SessionLocal() as db3:
        from app.services.charging_service import finalize_session
        from app.models.hardware import StationTelemetry
        sess = await db3.get(ChargingSession, sim.session_id)
        last_tel = (await db3.execute(
            select(StationTelemetry).where(StationTelemetry.station_id == sess.station_id)
            .order_by(StationTelemetry.timestamp.desc()).limit(1))).scalar_one_or_none()
        reason = StopReason(sim.stop_reason or StopReason.vehicle.value)
        meter_end = Decimal(str(last_tel.energy_total_kwh)) if last_tel and last_tel.energy_total_kwh else None
        await finalize_session(db3, sess, meter_end_kwh=meter_end, reason=reason)
        await db3.commit()
    simulator_manager.finish(sim.session_id)
