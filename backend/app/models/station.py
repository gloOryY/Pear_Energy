from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, Enum as SAEnum, JSON

from app.db.base import Base, TimestampMixin
from app.models.enums import ConnectorType, StationStatus


class Station(Base, TimestampMixin):
    __tablename__ = "stations"

    id: Mapped[str] = mapped_column(primary_key=True)
    location_id: Mapped[str] = mapped_column(ForeignKey("locations.id"), index=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)  # CP-MSK-001, РЅР° QR-РєРѕРґРµ
    name: Mapped[str] = mapped_column(String(255))
    serial_number: Mapped[str] = mapped_column(String(64), unique=True)
    device_token: Mapped[str] = mapped_column(String(128))  # С‚РѕРєРµРЅ Р¶РµР»РµР·Р° (РІ РїСЂРѕРґРµ С…СЂР°РЅРёС‚СЊ С…СЌС€)
    connector_type: Mapped[ConnectorType] = mapped_column(
        Enum(ConnectorType, name="connector_type_enum"), default=ConnectorType.type2
    )
    max_power_kw: Mapped[float] = mapped_column(Numeric(6, 2))
    max_current_a: Mapped[float] = mapped_column(Numeric(6, 1), default=32.0)
    status: Mapped[StationStatus] = mapped_column(Enum(StationStatus, name="station_status"), default=StationStatus.offline)
    
    # Р¤РѕС‚РѕРіСЂР°С„РёСЏ СЃС‚Р°РЅС†РёРё
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # РўР°СЂРёС„РёРєР°С†РёСЏ
    tariff_start: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)             # Р Р°Р·РѕРІР°СЏ РїР»Р°С‚Р° Р·Р° СЃС‚Р°СЂС‚
    tariff_per_minute: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)        # РџРѕРјРёРЅСѓС‚РЅР°СЏ РѕРїР»Р°С‚Р° Р·Р°СЂСЏРґРєРё
    tariff_per_kwh: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)           # РћРїР»Р°С‚Р° Р·Р° РєР’С‚В·С‡
    tariff_per_minute_idle: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)   # РџР»Р°С‚Р° Р·Р° РїСЂРѕСЃС‚РѕР№
    min_launch_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=100.0)      # РњРёРЅ. Р±Р°Р»Р°РЅСЃ РґР»СЏ Р°РєС‚РёРІР°С†РёРё
    booking_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    
    supports_booking: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    parking_info: Mapped[str] = mapped_column(Text, default="")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    latitude: Mapped[float] = mapped_column(Numeric(9, 6))
    longitude: Mapped[float] = mapped_column(Numeric(9, 6))

    location = relationship("Location", back_populates="stations")
    connectors = relationship("Connector", back_populates="station", cascade="all, delete-orphan", lazy="selectin")

    connectors = relationship("Connector", back_populates="station", cascade="all, delete-orphan", lazy="selectin")


class Connector(Base, TimestampMixin):
    __tablename__ = "connectors"

    id: Mapped[str] = mapped_column(primary_key=True)
    station_id: Mapped[str] = mapped_column(ForeignKey("stations.id", ondelete="CASCADE"), index=True)
    connector_number: Mapped[int] = mapped_column(default=1)
    type: Mapped[ConnectorType] = mapped_column(Enum(ConnectorType, name="connector_type_enum"))
    max_power_kw: Mapped[float] = mapped_column(Numeric(6, 2))
    status: Mapped[str] = mapped_column(String(32), default="available")
    current_session_id: Mapped[str | None] = mapped_column(ForeignKey("charging_sessions.id"), nullable=True)

    station = relationship("Station", back_populates="connectors")
