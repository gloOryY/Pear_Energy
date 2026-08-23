from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel
from app.models.enums import ConnectorType, UserRole


class VehicleIn(BaseModel):
    brand: str = Field(min_length=1, max_length=64)
    model: str = ""
    plate_number: str = ""
    connector_type: ConnectorType = ConnectorType.type2


class VehicleOut(VehicleIn, ORMModel):
    id: str


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    phone: str | None = Field(default=None, pattern=r"^\+7\d{10}$")
    email: EmailStr | None = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)


class UserOut(ORMModel):
    id: str
    phone: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    vehicles: list[VehicleOut] = []


class NotificationOut(ORMModel):
    id: str
    title: str
    body: str
    is_read: bool
