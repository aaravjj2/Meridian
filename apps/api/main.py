from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from apps.api.deps import get_mode, is_demo_mode
from apps.api.routers.markets import router as markets_router
from apps.api.routers.regime import router as regime_router
from apps.api.routers.research import router as research_router
from apps.api.routers.screener import router as screener_router
from meridian.agent.react import ResearchAgent
from meridian.agent.tools import ToolExecutor
from meridian.agent.websocket import (
    connection_manager,
    handle_websocket_message,
    stream_research_over_websocket,
)

app = FastAPI(
    title="Meridian API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(research_router, prefix="/api/v1")
app.include_router(screener_router, prefix="/api/v1")
app.include_router(regime_router, prefix="/api/v1")
app.include_router(markets_router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "mode": get_mode(),
        "version": "0.1.0",
    }


@app.get("/api/v1/metadata")
async def metadata() -> dict[str, object]:
    return {
        "version": "0.1.0",
        "model": "glm-5.1",
        "demo": is_demo_mode(),
        "data_sources": ["fred", "kalshi", "polymarket", "edgar", "news"],
        "websocket_supported": True,
    }


@app.websocket("/api/v1/ws/research")
async def websocket_research_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time GLM-5.1 agent streaming.

    Connect with: ws://localhost:8000/api/v1/ws/research

    Message format (client -> server):
    {
        "type": "query",
        "question": "What is the recession probability?"
    }

    Message format (server -> client):
    {
        "type": "trace",
        "data": { ... TraceStep ... },
        "timestamp": "2026-04-02T..."
    }

    Supported client message types:
    - "ping": Health check
    - "query": Start a new research query
    - "status": Get current status

    Supported server message types:
    - "connected": Initial connection acknowledgment
    - "trace": Trace step from agent reasoning
    - "reflection_checkpoint": Self-reflection checkpoint
    - "complete": Research complete
    - "error": Error occurred
    """
    # Create agent instance for this connection
    demo_mode = is_demo_mode()
    agent = ResearchAgent(demo_mode=demo_mode)

    await websocket.accept()

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "timestamp": "2026-04-02T00:00:00Z",
            "capabilities": ["trace", "reflection", "query"],
        })

        # Message loop
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                response = await handle_websocket_message(websocket, message, agent)

                # Send response for synchronous messages
                if message.get("type") in ["ping", "status"]:
                    await websocket.send_json(response)

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format",
                })
            except Exception as exc:
                await websocket.send_json({
                    "type": "error",
                    "message": str(exc),
                })

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        try:
            await websocket.close()
        except:
            pass


@app.websocket("/api/v1/ws/broadcast")
async def websocket_broadcast_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for broadcast updates.

    Connect to receive:
    - Real-time market data updates
    - System announcements
    - Collaborative updates

    This uses the connection manager for multi-client support.
    """
    import uuid

    connection_id = str(uuid.uuid4())
    await connection_manager.connect(connection_id, websocket)

    try:
        await websocket.send_json({
            "type": "connected",
            "connection_id": connection_id,
            "active_connections": connection_manager.get_connection_count(),
        })

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "connections": connection_manager.get_connection_count(),
                })

    except WebSocketDisconnect:
        connection_manager.disconnect(connection_id)
    except Exception:
        connection_manager.disconnect(connection_id)
    finally:
        try:
            await websocket.close()
        except:
            pass
