from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import ConnectorType, StationStatus


# --- Коннекторы ---

class ConnectorBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")
    connector_number: int = Field(default=1, ge=1)
    type: ConnectorType = ConnectorType.type2
    max_power_kw: Decimal = Field(default=Decimal("22.0"), gt=0)
    status: str = Field(default="available")


class ConnectorCreate(ConnectorBase):
    pass


class ConnectorResponse(ConnectorBase):
    model_config = ConfigDict(from_attributes=True, extra="allow")
    id: str
    station_id: str
    current_session_id: Optional[str] = None


# --- Основные схемы станций ---

class StationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")
    name: str = Field(..., max_length=255)
    location_id: Optional[str] = None
    public_id: Optional[str] = None
    serial_number: Optional[str] = None
    device_token: Optional[str] = None
    connector_type: Optional[ConnectorType] = ConnectorType.type2
    max_power_kw: Decimal = Field(default=Decimal("22.0"), gt=0)
    max_current_a: Decimal = Field(default=Decimal("32.0"), gt=0)
    status: StationStatus = StationStatus.offline

    # Новые поля
    image_url: Optional[str] = None
    tariff_start: Decimal = Field(default=Decimal("0.00"), ge=0)
    tariff_per_minute: Decimal = Field(default=Decimal("0.00"), ge=0)

    # Существующие тарифы и геопозиция
    tariff_per_kwh: Decimal = Field(default=Decimal("0.00"), ge=0)
    tariff_per_minute_idle: Decimal = Field(default=Decimal("0.00"), ge=0)
    min_launch_amount: Decimal = Field(default=Decimal("100.00"), ge=0)
    booking_amount: Decimal = Field(default=Decimal("0.00"), ge=0)

    supports_booking: bool = True
    is_active: bool = True
    parking_info: Optional[str] = ""
    address: Optional[str] = None
    city: Optional[str] = None
    latitude: Decimal
    longitude: Decimal


class StationCreate(StationBase):
    connectors: List[ConnectorCreate] = Field(default_factory=list)


class StationUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")
    name: Optional[str] = None
    location_id: Optional[str] = None
    public_id: Optional[str] = None
    serial_number: Optional[str] = None
    device_token: Optional[str] = None
    connector_type: Optional[ConnectorType] = None
    max_power_kw: Optional[Decimal] = None
    max_current_a: Optional[Decimal] = None
    status: Optional[StationStatus] = None
    image_url: Optional[str] = None
    tariff_start: Optional[Decimal] = None
    tariff_per_minute: Optional[Decimal] = None
    tariff_per_kwh: Optional[Decimal] = None
    tariff_per_minute_idle: Optional[Decimal] = None
    min_launch_amount: Optional[Decimal] = None
    booking_amount: Optional[Decimal] = None
    supports_booking: Optional[bool] = None
    is_active: Optional[bool] = None
    parking_info: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    connectors: Optional[List[ConnectorCreate]] = None


class StationResponse(StationBase):
    model_config = ConfigDict(from_attributes=True, extra="allow")
    id: str
    last_seen_at: Optional[datetime] = None
    connectors: List[ConnectorResponse] = []


# --- Схемы, используемые в stations.py и operator.py ---

class StationShort(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")
    id: str
    public_id: Optional[str] = None
    name: str
    status: Optional[Any] = None
    latitude: Decimal
    longitude: Decimal
    address: Optional[str] = None
    max_power_kw: Optional[Decimal] = None
    tariff_per_kwh: Optional[Decimal] = None
    tariff_start: Optional[Decimal] = None
    tariff_per_minute: Optional[Decimal] = None
    image_url: Optional[str] = None


class StationDetail(StationResponse):
    pass


class StationListItem(StationResponse):
    pass


class AvailabilityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")
    station_id: str
    is_available: bool = True
    available_connectors: int = 0
    total_connectors: int = 0
    status: Optional[str] = "available"


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")
    id: Optional[str] = None
    station_id: Optional[str] = None
    user_id: Optional[str] = None
    rating: Optional[int] = 5
    comment: Optional[str] = None
    created_at: Optional[datetime] = None