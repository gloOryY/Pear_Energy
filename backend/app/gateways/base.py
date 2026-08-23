from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class StationStatusInfo:
    status: str
    evse_state: str | None = None
    error_code: str | None = None


class StationGateway(ABC):
    """Интерфейс взаимодействия с аппаратной частью зарядной станции."""

    @abstractmethod
    async def send_start_command(self, station_id: str, session_id: str,
                                  limit_type: str, limit_value: Decimal) -> None: ...

    @abstractmethod
    async def send_stop_command(self, station_id: str, session_id: str, reason: str) -> None: ...

    @abstractmethod
    async def get_status(self, station_id: str) -> StationStatusInfo: ...
