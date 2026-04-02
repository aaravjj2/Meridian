"""
WebSocket support for real-time GLM-5.1 agent streaming.

This module provides WebSocket endpoints for real-time streaming
of agent reasoning traces without Server-Sent Events overhead.
"""

from __future__ import annotations

import json
import asyncio
from typing import Any
from datetime import UTC, datetime

from fastapi import WebSocket, WebSocketDisconnect

from meridian.agent.react import ResearchAgent
from meridian.agent.tools import ToolExecutor
from meridian.normalisation.schemas import TraceStep


def _iso_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


async def stream_research_over_websocket(
    websocket: WebSocket,
    question: str,
    agent: ResearchAgent,
) -> None:
    """
    Stream research results over WebSocket connection.

    This provides a bidirectional communication channel for
    real-time agent reasoning traces with lower latency than SSE.
    """
    await websocket.accept()

    try:
        # Send initial acknowledgment
        await websocket.send_json({
            "type": "connected",
            "timestamp": _iso_now(),
            "question": question,
        })

        # Stream trace steps
        step_count = 0
        async for step in agent.run(question):
            step_count += 1

            # Convert Pydantic model to dict
            step_dict = step.model_dump()

            # Send as JSON message
            await websocket.send_json({
                "type": "trace",
                "data": step_dict,
                "timestamp": _iso_now(),
            })

            # Handle reflection checkpoints specially
            if step.type == "reflection":
                await websocket.send_json({
                    "type": "reflection_checkpoint",
                    "step": step_count,
                    "message": step.content,
                    "timestamp": _iso_now(),
                })

        # Send completion message
        await websocket.send_json({
            "type": "complete",
            "total_steps": step_count,
            "timestamp": _iso_now(),
        })

    except WebSocketDisconnect:
        # Client disconnected
        pass
    except Exception as exc:
        # Send error message
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(exc),
                "timestamp": _iso_now(),
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


async def handle_websocket_message(
    websocket: WebSocket,
    message: dict[str, Any],
    agent: ResearchAgent | None = None,
) -> dict[str, Any]:
    """
    Handle incoming WebSocket messages from client.

    Supported message types:
    - "ping": Health check
    - "query": Start a new research query
    - "cancel": Cancel ongoing query
    - "status": Get current status
    """
    msg_type = message.get("type")

    if msg_type == "ping":
        return {
            "type": "pong",
            "timestamp": _iso_now(),
        }

    if msg_type == "status":
        return {
            "type": "status",
            "status": "ready",
            "model": "glm-5.1",
            "timestamp": _iso_now(),
        }

    if msg_type == "query" and agent:
        question = message.get("question", "")
        if not question:
            return {
                "type": "error",
                "message": "Question is required",
            }

        # Start streaming (this will run in background)
        asyncio.create_task(stream_research_over_websocket(websocket, question, agent))

        return {
            "type": "query_started",
            "question": question,
        }

    return {
        "type": "error",
        "message": f"Unknown message type: {msg_type}",
    }


class WebSocketConnectionManager:
    """
    Manage WebSocket connections for broadcasting updates.

    Useful for:
    - Multi-user collaboration
    - Real-time market data updates
    - Broadcast announcements
    """

    def __init__(self) -> None:
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, connection_id: str, websocket: WebSocket) -> None:
        """Register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket

    def disconnect(self, connection_id: str) -> None:
        """Unregister a WebSocket connection."""
        self.active_connections.pop(connection_id, None)

    async def send_personal_message(self, message: dict[str, Any], connection_id: str) -> None:
        """Send a message to a specific connection."""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_json(message)
            except:
                self.disconnect(connection_id)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all active connections."""
        disconnected = []
        for connection_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection_id)

        # Clean up disconnected clients
        for connection_id in disconnected:
            self.disconnect(connection_id)

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)


# Global connection manager instance
connection_manager = WebSocketConnectionManager()
