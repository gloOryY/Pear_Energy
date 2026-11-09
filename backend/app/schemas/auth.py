from pydantic import BaseModel, EmailStr, Field

PHONE_RE = r"^\+7\d{10}$"


class RegisterIn(BaseModel):
    phone: str = Field(pattern=PHONE_RE, examples=["+79001234567"])
    email: EmailStr
    password: str = Field(min_length=8, examples=["Password123!"])
    full_name: str = Field(min_length=2, max_length=255)
    catalog_car_id: int | None = None
    custom_car_make: str | None = None
    custom_car_model: str | None = None
    custom_car_battery_kwh: float | None = None
    custom_car_connector: str | None = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
