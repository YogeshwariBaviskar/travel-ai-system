"""WebSocket endpoint for real-time trip plan updates."""
import asyncio
import json
import os
from typing import Optional

import redis
import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import jwt, JWTError

from api.config import settings

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, trip_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(trip_id, []).append(ws)

    def disconnect(self, trip_id: str, ws: WebSocket) -> None:
        conns = self._connections.get(trip_id, [])
        if ws in conns:
            conns.remove(ws)
        if not conns:
            self._connections.pop(trip_id, None)

    async def broadcast(self, trip_id: str, message: dict) -> None:
        for ws in list(self._connections.get(trip_id, [])):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(trip_id, ws)


manager = ConnectionManager()

_redis_async: Optional[aioredis.Redis] = None


def _get_redis() -> aioredis.Redis:
    global _redis_async
    if _redis_async is None:
        _redis_async = aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    return _redis_async


async def _redis_listener(trip_id: str) -> None:
    """Subscribe to Redis channel and forward messages to connected WebSocket clients."""
    r = _get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe(f"trip:{trip_id}:updates")
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await manager.broadcast(trip_id, data)
    except asyncio.CancelledError:
        pass
    except Exception:
        pass
    finally:
        try:
            await pubsub.unsubscribe()
        except Exception:
            pass


def _verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except JWTError:
        return None


@router.websocket("/trips/{trip_id}")
async def trip_updates_ws(websocket: WebSocket, trip_id: str, token: str = ""):
    user_id = _verify_token(token)
    if not user_id:
        await websocket.accept()
        await websocket.close(code=4001)
        return

    await manager.connect(trip_id, websocket)
    listener_task = asyncio.create_task(_redis_listener(trip_id))

    try:
        await websocket.send_json({"event": "connected", "trip_id": trip_id})
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "ping":
                await websocket.send_json({"event": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(trip_id, websocket)
        listener_task.cancel()
