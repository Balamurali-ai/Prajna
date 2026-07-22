"""
====================================================
Dashboard WebSocket
====================================================
"""
from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Dict, Set

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger


class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"✅ WS connected. Total: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"❌ WS disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]) -> None:
        if not self.active_connections:
            return
        payload = json.dumps(
            {"timestamp": time.time(), **message},
            default=str,
        )
        dead = []
        for ws in list(self.active_connections):
            try:
                await ws.send_text(payload)
            except Exception as e:
                logger.warning(f"WS send failed: {e}")
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws)

    async def send_personal(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        try:
            await websocket.send_text(json.dumps(
                {"timestamp": time.time(), **message},
                default=str,
            ))
        except Exception as e:
            logger.warning(f"WS personal send failed: {e}")


manager = ConnectionManager()


async def dashboard_ws(websocket: WebSocket) -> None:
    """
    Dashboard WebSocket endpoint.
    """
    await manager.connect(websocket)
    subscribed_channels: Set[str] = set()

    try:
        await manager.send_personal(websocket, {
            "type": "connected",
            "message": "Connected to crime intelligence dashboard",
            "channels": ["risk_rankings", "hotspots", "reports", "alerts"],
        })

        heartbeat_task = asyncio.create_task(_heartbeat(websocket))

        while True:
            try:
                raw = await websocket.receive_text()
                msg = json.loads(raw)
                action = msg.get("action")

                if action == "ping":
                    await manager.send_personal(websocket, {"type": "pong"})
                elif action == "subscribe":
                    channel = msg.get("channel")
                    if channel:
                        subscribed_channels.add(channel)
                        await manager.send_personal(websocket, {
                            "type": "subscribed",
                            "channel": channel,
                        })
                elif action == "unsubscribe":
                    channel = msg.get("channel")
                    subscribed_channels.discard(channel)
                    await manager.send_personal(websocket, {
                        "type": "unsubscribed",
                        "channel": channel,
                    })
                else:
                    await manager.send_personal(websocket, {
                        "type": "error",
                        "message": f"Unknown action: {action}",
                    })
            except WebSocketDisconnect:
                raise
            except json.JSONDecodeError:
                await manager.send_personal(websocket, {
                    "type": "error",
                    "message": "Invalid JSON",
                })
            except Exception as e:
                logger.error(f"WS message error: {e}")
    except WebSocketDisconnect:
        pass
    finally:
        if not heartbeat_task.done():
            heartbeat_task.cancel()
        await manager.disconnect(websocket)


async def _heartbeat(websocket: WebSocket) -> None:
    try:
        while True:
            await asyncio.sleep(30)
            try:
                await websocket.send_text(json.dumps({
                    "type": "heartbeat",
                    "timestamp": time.time(),
                }))
            except Exception:
                break
    except asyncio.CancelledError:
        pass
