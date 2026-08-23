from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.common import ORMModel
from app.models.enums import ConnectorType, StationStatus


class StationShort(ORMModel):
    id: str
    public_id: str
    name: str
    status: StationStatus
    latitude: Decimal
    longitude: Decimal
    max_power_kw: Decimal
    tariff_per_kwh: Decimal
    supports_booking: bool
    city: str | None = None
    address: str | None = None
    photo: str | None = None


class ConnectorOut(ORMModel):
    id: str
    connector_number: int
    type: ConnectorType
    max_power_kw: Decimal
    status: str


class ReviewOut(ORMModel):
    id: str
    rating: int
    text: str
    created_at: datetime
    author: str | None = None


class StationDetail(ORMModel):
    id: str
    public_id: str
    name: str
    serial_number: str
    connector_type: ConnectorType
    max_power_kw: Decimal
    max_current_a: Decimal
    status: StationStatus
    tariff_per_kwh: Decimal
    tariff_per_minute_idle: Decimal
    min_launch_amount: Decimal
    booking_amount: Decimal
    supports_booking: bool
    is_active: bool
    parking_info: str
    last_seen_at: datetime | None
    latitude: Decimal
    longitude: Decimal
    location_name: str = ""
    address: str = ""
    city: str = ""
    description: str = ""
    amenities: list[str] = []
    schedule: dict = {}
    venue_types: list[str] = []
    photos: list[str] = []
    connectors: list[ConnectorOut] = []


class AvailabilityOut(BaseModel):
    status: StationStatus
    bookings: list[dict] = []
