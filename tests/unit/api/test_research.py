from __future__ import annotations

import hashlib
import json

from fastapi.testclient import TestClient

from apps.api.main import app
from meridian.normalisation.schemas import ResearchBrief


client = TestClient(app)


def _collect_events(question: str, session_id: str | None = None) -> list[dict]:
    events: list[dict] = []
    payload = {
        "question": question,
        "mode": "demo",
    }
    if session_id:
        payload["session_id"] = session_id

    with client.stream("POST", "/api/v1/research", json=payload) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        for line in response.iter_lines():
            if not line or not line.startswith("data: "):
                continue
            event = json.loads(line[6:])
            events.append(event)

    return events


def _brief_signature(brief_payload: dict) -> str:
    canonical = {
        "query_class": brief_payload.get("query_class"),
        "thesis": brief_payload.get("thesis"),
        "bull_case": brief_payload.get("bull_case"),
        "bear_case": brief_payload.get("bear_case"),
        "key_risks": brief_payload.get("key_risks"),
        "sources": [
            {
                "type": source.get("type"),
                "id": source.get("id"),
                "claim_refs": source.get("claim_refs", []),
            }
            for source in brief_payload.get("sources", [])
        ],
    }
    digest = hashlib.sha256(json.dumps(canonical, sort_keys=True).encode("utf-8"))
    return digest.hexdigest()


def test_research_sse_stream_emits_complete() -> None:
    events = _collect_events(
        question="What does the current yield curve shape imply for equities over the next 6 months?",
        session_id="phase2-stream-test",
    )

    assert len(events) >= 5
    assert events[-1]["type"] == "complete"
    assert events[-1].get("session_id") == "phase2-stream-test"

    complete = events[-1]
    brief = ResearchBrief.model_validate(complete["brief"])
    assert brief.thesis
    assert brief.query_class == "macro_outlook"
    assert len(brief.sources) >= 3


def test_research_sse_contains_required_event_types() -> None:
    seen = set()
    events = _collect_events(question="Yield curve outlook?", session_id="phase2-types-test")
    for payload in events:
        seen.add(payload["type"])

    required = {"tool_call", "tool_result", "reasoning", "brief_delta", "complete"}
    assert required.issubset(seen)


def test_research_followup_uses_session_context() -> None:
    session_id = "phase2-followup-session"

    _collect_events(
        question="Give me a macro outlook for the next two quarters.",
        session_id=session_id,
    )
    events = _collect_events(
        question="How should I interpret the event probability if inflation re-accelerates?",
        session_id=session_id,
    )

    complete = events[-1]
    assert complete["type"] == "complete"
    assert complete.get("followup") is True
    assert complete.get("session_context_used") is True

    brief = ResearchBrief.model_validate(complete["brief"])
    assert brief.query_class == "event_probability"
    assert brief.follow_up_context is not None
    assert "follow-up to prior question" in brief.follow_up_context.lower()


def test_research_demo_output_is_deterministic_for_same_question() -> None:
    events_a = _collect_events(
        question="Frame AAPL versus macro conditions for a cautious equity book.",
        session_id="phase2-determinism-a",
    )
    events_b = _collect_events(
        question="Frame AAPL versus macro conditions for a cautious equity book.",
        session_id="phase2-determinism-b",
    )

    brief_a = events_a[-1]["brief"]
    brief_b = events_b[-1]["brief"]

    assert _brief_signature(brief_a) == _brief_signature(brief_b)
