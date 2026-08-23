import httpx

from app.gateways.base import StationGateway, StationStatusInfo


class HttpStationGateway(StationGateway):
    """Реальная станция (ESP32): сама опрашивает GET /api/v1/stations/{public_id}/commands/next
    с заголовком X-Station-Token и шлёт результаты в /command-result и телеметрию в /telemetry.
    Шлюз здесь только фиксирует факт постановки команды."""
    name = "http"

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url

    async def send_start_command(self, station_id, session_id, limit_type, limit_value) -> None:
        return None  # устройство само заберёт команду через polling

    async def send_stop_command(self, station_id, session_id, reason) -> None:
        return None

    async def get_status(self, station_id) -> StationStatusInfo:
        if not self.base_url:
            return StationStatusInfo(status="unknown")
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                r = await client.get(f"{self.base_url}/stations/{station_id}/status")
                r.raise_for_status()
                d = r.json()
                return StationStatusInfo(status=d.get("status", "unknown"),
                                          evse_state=d.get("evse_state"),
                                          error_code=d.get("error_code"))
        except Exception:
            return StationStatusInfo(status="offline")


def get_station_gateway():
    from app.core.config import settings
    return MockStationGateway() if settings.STATION_MODE == "mock" else HttpStationGateway()
