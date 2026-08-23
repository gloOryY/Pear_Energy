"""Мост между бизнес-логикой и WS-соединениями через Redis pub/sub.
Работает и при нескольких репликах backend: событие публикуется в Redis,
каждый инстанс backend доставляет его своим локальным соединениям."""
import asyncio
import json
import logging

from app.ws.manager import manager

log = logging.getLogger("eventbus")

_local_loop: asyncio.AbstractEventLoop | None = None


def set_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _local_loop
    _local_loop = loop


async def publish(channels: list[str], payload: dict) -> None:
    from app.db.session import get_redis
    redis = get_redis()
    msg = json.dumps(payload, default=str)
    for ch in channels:
        try:
            await redis.publish(f"ws:{ch}", msg)
        except Exception:
            log.exception("publish failed %s", ch)


async def start_reader() -> None:
    from app.db.session import get_redis
    redis = get_redis()
    pubsub = redis.pubsub()
    await pubsub.psubscribe("ws:*")
    log.info("EventBus reader started")
    async for msg in pubsub.listen():
        if msg["type"] != "pmessage":
            continue
        channel: str = msg["channel"].removeprefix("ws:")
        try:
            payload = json.loads(msg["data"])
        except Exception:
            continue
        await manager.broadcast(channel, payload)
