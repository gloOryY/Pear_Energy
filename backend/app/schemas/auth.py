from pydantic import BaseModel, EmailStr, Field

PHONE_RE = r"^\+7\d{10}$"


class RegisterIn(BaseModel):
    phone: str = Field(pattern=PHONE_RE, examples=["+79001234567"])
    email: EmailStr
    password: str = Field(min_length=8, examples=["Password123!"])
    full_name: str = Field(min_length=2, max_length=255)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
