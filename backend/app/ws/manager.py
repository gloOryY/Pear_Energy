import asyncio
import json
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.channels: dict[str, set[WebSocket]] = defaultdict(set)
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def connect(self, channel: str, ws: WebSocket) -> None:
        await ws.accept()
        async with self._locks[channel]:
            self.channels[channel].add(ws)

    async def disconnect(self, channel: str, ws: WebSocket) -> None:
        async with self._locks[channel]:
            self.channels[channel].discard(ws)
            if not self.channels[channel]:
                self.channels.pop(channel, None)

    async def broadcast(self, channel: str, payload: dict) -> int:
        dead: list[WebSocket] = []
        sockets = list(self.channels.get(channel, ()))
        for ws in sockets:
            try:
                await ws.send_text(json.dumps(payload, default=str))
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(channel, ws)
        return len(sockets) - len(dead)


manager = ConnectionManager()
