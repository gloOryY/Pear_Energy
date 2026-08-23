import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_ctx = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_ctx.verify(password, password_hash)


def _encode(sub: str, typ: str, ttl: timedelta, extra: dict[str, Any] | None = None) -> tuple[str, str]:
    jti = uuid.uuid4().hex
    now = datetime.now(timezone.utc)
    payload = {"sub": sub, "typ": typ, "jti": jti, "iat": now, "exp": now + ttl}
    if extra:
        payload |= extra
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM), jti


def decode_token(token: str, expected_typ: str) -> dict[str, Any]:
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    if payload.get("typ") != expected_typ:
        raise jwt.InvalidTokenError("wrong token type")
    return payload


def create_access_token(user_id: str, role: str) -> str:
    token, _ = _encode(user_id, "access", timedelta(minutes=settings.ACCESS_TOKEN_TTL_MIN), {"role": role})
    return token


def create_refresh_token(user_id: str) -> str:
    token, _ = _encode(user_id, "refresh", timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS))
    return token
