from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import LimitType, SessionStatus, StopReason


class ChargingSession(Base, TimestampMixin):
    __tablename__ = "charging_sessions"

    id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    station_id: Mapped[str] = mapped_column(ForeignKey("stations.id"), index=True)
    connector_id: Mapped[str | None] = mapped_column(ForeignKey("connectors.id"), nullable=True)
    payment_id: Mapped[str | None] = mapped_column(ForeignKey("payments.id"), nullable=True)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status"), default=SessionStatus.awaiting_payment
    )
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meter_start_kwh: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    meter_end_kwh: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    energy_kwh: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=0)
    tariff_per_kwh: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    stop_reason: Mapped[StopReason | None] = mapped_column(Enum(StopReason, name="stop_reason"), nullable=True)
    selected_limit_type: Mapped[LimitType] = mapped_column(Enum(LimitType, name="limit_type"))
    selected_limit_value: Mapped[Decimal] = mapped_column(Numeric(12, 3))

    station = relationship("Station", lazy="selectin")
    user = relationship("User", lazy="selectin")
