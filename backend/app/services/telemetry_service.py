from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import utcnow
from app.models.charging import ChargingSession
from app.models.enums import SessionStatus, StationStatus, StopReason
from app.models.hardware import StationTelemetry
from app.models.station import Station
from app.ws.eventbus import publish

EVSE_TO_STATION = {
    "available": StationStatus.available,
    "vehicle_connected": StationStatus.vehicle_connected,
    "awaiting_payment": StationStatus.awaiting_payment,
    "preparing": StationStatus.preparing,
    "charging": StationStatus.charging,
    "suspended_ev": StationStatus.suspended_ev,
    "finishing": StationStatus.finishing,
    "unavailable": StationStatus.unavailable,
    "faulted": StationStatus.faulted,
    "emergency_stop": StationStatus.emergency_stop,
}


async def ingest_telemetry(db: AsyncSession, station: Station, data: dict) -> dict:
    from app.services.charging_service import request_stop

    row = StationTelemetry(
        station_id=station.id,
        voltage_v=data.get("voltage_v"), current_a=data.get("current_a"),
        power_kw=data.get("power_kw"), energy_total_kwh=data.get("energy_total_kwh"),
        temperature_c=data.get("temperature_c"), evse_state=data.get("evse_state"),
        error_code=data.get("error_code"),
    )
    db.add(row)
    station.last_seen_at = utcnow()

    evse = data.get("evse_state")
    if evse in EVSE_TO_STATION and station.status not in (
            StationStatus.unavailable, StationStatus.emergency_stop):
        station.status = EVSE_TO_STATION[evse]

    session = (await db.execute(
        select(ChargingSession).where(
            ChargingSession.station_id == station.id,
            ChargingSession.status.in_((SessionStatus.charging,)),
        ))).scalars().first()

    payload_out = {"type": "telemetry", "station_public_id": station.public_id,
                   "power_kw": data.get("power_kw"), "current_a": data.get("current_a"),
                   "voltage_v": data.get("voltage_v"), "evse_state": evse}

    if session and session.meter_start_kwh is not None and data.get("energy_total_kwh") is not None:
        energy = max(Decimal(0), Decimal(str(data["energy_total_kwh"])) - session.meter_start_kwh)
        session.energy_kwh = energy.quantize(Decimal("0.001"))
        session.total_amount = (energy * session.tariff_per_kwh).quantize(Decimal("0.01"))
        payload_out |= {"session_id": session.id, "energy_kwh": str(session.energy_kwh),
                        "total_amount": str(session.total_amount)}

    if data.get("error_code") or evse in ("faulted", "emergency_stop"):
        if session:
            await request_stop(db, session, StopReason.fault)
        station.status = StationStatus.faulted

    channels = [f"station:{station.public_id}"] + ([f"user:{session.user_id}"] if session else [])
    await publish(channels, payload_out)
    return payload_out


async def heartbeat(db: AsyncSession, station: Station) -> None:
    station.last_seen_at = utcnow()
    if station.status == StationStatus.offline:
        station.status = StationStatus.available
