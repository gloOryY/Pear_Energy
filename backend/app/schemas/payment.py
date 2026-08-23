from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.common import ORMModel
from app.models.enums import PaymentMethod, PaymentStatus


class PaymentCreateIn(BaseModel):
    session_id: str
    method: PaymentMethod
    return_url: str | None = None


class ConfirmationOut(BaseModel):
    type: str
    sbp_payload: str | None = None
    url: str | None = None


class PaymentOut(ORMModel):
    id: str
    session_id: str | None
    provider: str
    method: PaymentMethod
    amount: Decimal
    currency: str
    status: PaymentStatus
    paid_at: datetime | None
    created_at: datetime
    description: str


class CheckoutOut(BaseModel):
    payment: PaymentOut
    confirmation: ConfirmationOut
