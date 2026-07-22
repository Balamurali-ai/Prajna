"""
====================================================
Dashboard WebSocket
====================================================
Pushes real-time updates to the SPA:
- Risk ranking changes
- New hotspots
- Report completion events
- System alerts
====================================================
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any, Dict, Set

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from app.core.security import validate_supabase_token
from app.core.exceptions import AuthenticationException


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
        """Send a message to all connected clients."""
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


# ====================================================
# Global Manager
# ====================================================
manager = ConnectionManager()


# ====================================================
# WebSocket Route
# =====================================================
async def dashboard_ws(websocket: WebSocket) -> None:
    """
    Dashboard WebSocket endpoint.

    Client → Server messages:
    - {"action": "subscribe", "channel": "risk_rankings"}
    - {"action": "subscribe", "channel": "hotspots"}
    - {"action": "subscribe", "channel": "reports"}
    - {"action": "ping"}

    Server → Client messages:
    - {"type": "risk_update", "data": {...}}
    - {"type": "hotspot_update", "data": {...}}
    - {"type": "report_complete", "data": {...}}
    - {"type": "pong"}

    Auth: client must pass ``?token=<jwt>`` (Supabase access token).
    Phase 8: the token is validated before the connection is accepted.
    In dev mode (``APP_ENV=development`` and ``ALLOW_WS_DEV_BYPASS=1``)
    the token check is skipped for easier local testing.
    """
    # --- Phase 8: JWT validation ---
    from app.core.config import settings  # local import to avoid cycle
    token = websocket.query_params.get("token")
    authed = False
    if token:
        try:
            validate_supabase_token(token)
            authed = True
        except AuthenticationException as e:
            logger.warning(f"WS auth failed: {e}")
            authed = False

    allow_bypass = (
        settings.APP_ENV == "development"
        and os.getenv("ALLOW_WS_DEV_BYPASS", "1") == "1"
    )
    if not authed and not allow_bypass:
        await websocket.close(code=1008, reason="Unauthorized")
        logger.warning("❌ WS rejected: no valid token")
        return

    await manager.connect(websocket)
    subscribed_channels: Set[str] = set()

    try:
        # Send welcome message
        await manager.send_personal(websocket, {
            "type": "connected",
            "message": "Connected to crime intelligence dashboard",
            "channels": ["risk_rankings", "hotspots", "reports", "alerts"],
        })

        # Start heartbeat task
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
    """Send periodic heartbeat to keep connection alive."""
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
