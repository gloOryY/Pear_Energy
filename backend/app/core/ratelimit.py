from fastapi import HTTPException, Request

from app.core.config import settings
from app.db.session import get_redis


async def rate_limit_auth(request: Request) -> None:
    """Скользящее окно 60 с на IP для чувствительных эндпоинтов."""
    redis = get_redis()
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
        request.client.host if request.client else "unknown"
    )
    key = f"rl:auth:{ip}:{request.url.path}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 60)
    if count > settings.RATE_LIMIT_AUTH_PER_MIN:
        raise HTTPException(status_code=429, detail="Слишком много запросов, попробуйте позже")
