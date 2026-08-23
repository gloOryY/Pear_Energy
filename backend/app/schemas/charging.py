from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import ORMModel
from app.models.enums import LimitType, SessionStatus, StopReason


class QuoteIn(BaseModel):
    station_id: str
    limit_type: LimitType
    limit_value: Decimal = Field(gt=0)


class QuoteOut(BaseModel):
    station_id: str
    limit_type: LimitType
    limit_value: Decimal
    estimated_kwh: Decimal | None = None
    estimated_minutes: int | None = None
    estimated_amount: Decimal | None = None
    tariff_per_kwh: Decimal
    min_launch_amount: Decimal


class StartSessionIn(BaseModel):
    station_id: str
    limit_type: LimitType
    limit_value: Decimal = Field(gt=0)

    @model_validator(mode="after")
    def check_value(self):
        if self.limit_type == LimitType.minutes and not (5 <= float(self.limit_value) <= 12 * 60):
            raise ValueError("Лимит времени: от 5 минут до 12 часов")
        return self


class ExtendLimitIn(BaseModel):
    add_kwh: Decimal | None = Field(default=None, gt=0)
    add_rub: Decimal | None = Field(default=None, gt=0)


class SessionOut(ORMModel):
    id: str
    status: SessionStatus
    station_id: str
    start_at: datetime | None
    end_at: datetime | None
    energy_kwh: Decimal
    tariff_per_kwh: Decimal
    total_amount: Decimal
    stop_reason: StopReason | None
    selected_limit_type: LimitType
    selected_limit_value: Decimal
    payment_id: str | None


class TelemetryLive(BaseModel):
    power_kw: Decimal = Decimal(0)
    current_a: Decimal = Decimal(0)
    voltage_v: Decimal = Decimal(0)
    evse_state: str | None = None
    eta_minutes: int | None = None
