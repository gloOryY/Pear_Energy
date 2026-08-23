from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, utcnow


class StationTelemetry(Base):
    __tablename__ = "station_telemetry"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(ForeignKey("stations.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    voltage_v: Mapped[float | None] = mapped_column(Numeric(8, 1), nullable=True)
    current_a: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    power_kw: Mapped[float | None] = mapped_column(Numeric(8, 3), nullable=True)
    energy_total_kwh: Mapped[float | None] = mapped_column(Numeric(12, 3), nullable=True)
    temperature_c: Mapped[float | None] = mapped_column(Numeric(6, 1), nullable=True)
    evse_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)


class StationCommand(Base, TimestampMixin):
    __tablename__ = "station_commands"

    id: Mapped[str] = mapped_column(primary_key=True)
    station_id: Mapped[str] = mapped_column(ForeignKey("stations.id"), index=True)
    type: Mapped[str] = mapped_column(String(32))  # start|stop|reboot|lock|unlock|update_limits
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)
    created_by: Mapped[str | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
