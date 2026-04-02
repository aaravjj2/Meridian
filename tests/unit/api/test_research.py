from __future__ import annotations

import json

from fastapi.testclient import TestClient

from apps.api.main import app
from meridian.normalisation.schemas import ResearchBrief


client = TestClient(app)


def test_research_sse_stream_emits_complete() -> None:
    events: list[dict] = []

    with client.stream(
        "POST",
        "/api/v1/research",
        json={
            "question": "What does the current yield curve shape imply for equities over the next 6 months?",
            "mode": "demo",
        },
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        for line in response.iter_lines():
            if not line or not line.startswith("data: "):
                continue
            event = json.loads(line[6:])
            events.append(event)

    assert len(events) >= 5
    assert events[-1]["type"] == "complete"

    complete = events[-1]
    brief = ResearchBrief.model_validate(complete["brief"])
    assert brief.thesis
    assert len(brief.sources) >= 3


def test_research_sse_contains_required_event_types() -> None:
    seen = set()
    with client.stream(
        "POST",
        "/api/v1/research",
        json={"question": "Yield curve outlook?", "mode": "demo"},
    ) as response:
        for line in response.iter_lines():
            if not line or not line.startswith("data: "):
                continue
            payload = json.loads(line[6:])
            seen.add(payload["type"])

    required = {"tool_call", "tool_result", "reasoning", "brief_delta", "complete"}
    assert required.issubset(seen)
