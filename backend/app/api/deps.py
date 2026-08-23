import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.models import User
from app.models.enums import UserRole

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Не авторизован")
    try:
        payload = decode_token(creds.credentials, "access")
    except pyjwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Токен недействителен или истёк")
    user = await db.get(User, payload["sub"])
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Учётная запись недоступна")
    return user


def require_roles(*roles: UserRole):
    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Недостаточно прав")
        return user
    return checker


require_driver = require_roles(UserRole.driver, UserRole.operator, UserRole.admin)
require_operator = require_roles(UserRole.operator, UserRole.admin)
require_admin = require_roles(UserRole.admin)


async def get_station_device(public_id: str, x_station_token: str,
                              db: AsyncSession = Depends(get_db)):
    """Аутентификация железа станции."""
    from app.models.station import Station
    res = await db.execute(select(Station).where(Station.public_id == public_id))
    station = res.scalar_one_or_none()
    if station is None or station.device_token != x_station_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Неверный токен станции")
    return station
