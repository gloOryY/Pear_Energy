from sqlalchemy import JSON
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.enums import PaymentMethod, PaymentStatus


class PaymentIntent(Base, TimestampMixin):
    __tablename__ = "payment_intents"

    id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod, name="payment_method"))
    status: Mapped[str] = mapped_column(String(32), default="created")
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(primary_key=True)
    intent_id: Mapped[str | None] = mapped_column(ForeignKey("payment_intents.id"), nullable=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    session_id: Mapped[str | None] = mapped_column(ForeignKey("charging_sessions.id"), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(32), default="mock")
    provider_payment_id: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True, index=True)
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod, name="payment_method"))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"), default=PaymentStatus.pending
    )
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)
    confirmation_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    sbp_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")


class PaymentWebhook(Base, TimestampMixin):
    __tablename__ = "payment_webhooks"

    id: Mapped[str] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), index=True)
    event_type: Mapped[str] = mapped_column(String(64))
    provider_payment_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    payload: Mapped[dict] = mapped_column(
    JSON,
    nullable=False,
    default=dict,)
    processed: Mapped[bool] = mapped_column(default=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class Refund(Base, TimestampMixin):
    __tablename__ = "refunds"

    id: Mapped[str] = mapped_column(primary_key=True)
    payment_id: Mapped[str] = mapped_column(ForeignKey("payments.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    reason: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="succeeded")


class Receipt(Base, TimestampMixin):
    __tablename__ = "receipts"

    id: Mapped[str] = mapped_column(primary_key=True)
    payment_id: Mapped[str] = mapped_column(ForeignKey("payments.id"), index=True)
    session_id: Mapped[str | None] = mapped_column(index=True)
    number: Mapped[str] = mapped_column(String(32), unique=True)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
