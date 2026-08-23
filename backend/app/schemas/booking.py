from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, model_validator

from app.schemas.common import ORMModel
from app.models.enums import BookingStatus


class BookingIn(BaseModel):
    starts_at: datetime
    ends_at: datetime

    @model_validator(mode="after")
    def check_window(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("Окончание должно быть позже начала")
        if (self.ends_at - self.starts_at).total_seconds() > 24 * 3600:
            raise ValueError("Бронирование не длиннее 24 часов")
        return self


class BookingOut(ORMModel):
    id: str
    station_id: str
    starts_at: datetime
    ends_at: datetime
    status: BookingStatus
    amount: Decimal
