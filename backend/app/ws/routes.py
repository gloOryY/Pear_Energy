import jwt as pyjwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.ws.manager import manager

router = APIRouter()


@router.websocket("/ws/stations/{public_id}")
async def ws_station(ws: WebSocket, public_id: str):
    await manager.connect(f"station:{public_id}", ws)
    try:
        while True:
            await ws.receive_text()  # держим соединение, игнорируем пинги клиента
    except WebSocketDisconnect:
        await manager.disconnect(f"station:{public_id}", ws)


@router.websocket("/ws/users/{user_id}/sessions")
async def ws_user_sessions(ws: WebSocket, user_id: str, token: str = ""):
    try:
        payload = pyjwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except pyjwt.PyJWTError:
        await ws.close(code=4401)
        return
    if payload["sub"] != user_id and payload.get("role") != "admin":
        await ws.close(code=4403)
        return
    await manager.connect(f"user:{user_id}", ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(f"user:{user_id}", ws)
