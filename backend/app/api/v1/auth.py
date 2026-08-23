import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.ratelimit import rate_limit_auth
from app.core.security import (create_access_token, create_refresh_token,
                                decode_token, hash_password, verify_password)
from app.db.session import get_db, get_redis
from app.models import User
from app.models.enums import UserRole
from app.schemas.auth import LoginIn, RefreshIn, RegisterIn, TokenPair
from app.schemas.user import UserOut
from app.utils.audit import audit
from app.utils.ids import uid

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_TTL = settings.REFRESH_TOKEN_TTL_DAYS * 86400


async def _store_refresh(redis: Redis, token: str, user_id: str) -> None:
    payload = decode_token(token, "refresh")
    await redis.setex(f"refresh:{payload['jti']}", REFRESH_TTL, user_id)


async def _pair(redis: Redis, user: User, db: AsyncSession) -> TokenPair:
    access = create_access_token(str(user.id), user.role.value)
    refresh = create_refresh_token(str(user.id))
    await _store_refresh(redis, refresh, str(user.id))
    await audit(db, "auth.login", actor_id=str(user.id))
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/register", response_model=UserOut, status_code=201,
             dependencies=[Depends(rate_limit_auth)])
async def register(data: RegisterIn, db: AsyncSession = Depends(get_db)):
    dup = (await db.execute(
        select(User).where((User.email == data.email.lower()) | (User.phone == data.phone))
    )).scalar_one_or_none()
    if dup:
        raise HTTPException(409, "Пользователь с таким email или телефоном уже существует")
    user = User(id=uid(), phone=data.phone, email=data.email.lower(),
                password_hash=hash_password(data.password),
                full_name=data.full_name, role=UserRole.driver)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenPair, dependencies=[Depends(rate_limit_auth)])
async def login(data: LoginIn, db: AsyncSession = Depends(get_db),
                redis: Redis = Depends(get_redis)):
    user = (await db.execute(select(User).where(User.email == data.email.lower()))).scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Неверный email или пароль")
    if not user.is_active:
        raise HTTPException(403, "Учётная запись заблокирована")
    return await _pair(redis, user, db)


@router.post("/refresh", response_model=TokenPair)
async def refresh_tokens(data: RefreshIn, redis: Redis = Depends(get_redis),
                         db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(data.refresh_token, "refresh")
    except pyjwt.PyJWTError:
        raise HTTPException(401, "Refresh-токен недействителен")
    stored = await redis.get(f"refresh:{payload['jti']}")
    if not stored or stored != payload["sub"]:
        raise HTTPException(401, "Refresh-токен отозван")
    await redis.delete(f"refresh:{payload['jti']}")
    user = await db.get(User, payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(403, "Учётная запись недоступна")
    return await _pair(redis, user, db)


@router.post("/logout")
async def logout(data: RefreshIn, redis: Redis = Depends(get_redis)):
    try:
        payload = decode_token(data.refresh_token, "refresh")
        await redis.delete(f"refresh:{payload['jti']}")
    except pyjwt.PyJWTError:
        pass
    return {"ok": True}


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user
