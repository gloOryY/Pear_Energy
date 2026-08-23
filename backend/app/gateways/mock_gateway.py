from app.gateways.base import StationGateway, StationStatusInfo


class MockStationGateway(StationGateway):
    """Локальная разработка: команда кладётся в БД (её же забирает polling),
    а симулятор станции генерирует телеметрию и рост энергии."""
    name = "mock"

    async def send_start_command(self, station_id, session_id, limit_type, limit_value) -> None:
        from app.services.simulator import simulator_manager
        simulator_manager.launch(session_id=session_id)

    async def send_stop_command(self, station_id, session_id, reason) -> None:
        from app.services.simulator import simulator_manager
        simulator_manager.request_stop(session_id, reason)

    async def get_status(self, station_id) -> StationStatusInfo:
        return StationStatusInfo(status="available")
