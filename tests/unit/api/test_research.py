from __future__ import annotations

import hashlib
import json

from fastapi.testclient import TestClient

from apps.api.main import app
from meridian.normalisation.schemas import ResearchBrief


client = TestClient(app)


def _collect_events(
    question: str,
    session_id: str | None = None,
    template_id: str | None = None,
) -> list[dict]:
    events: list[dict] = []
    payload = {
        "question": question,
        "mode": "demo",
    }
    if session_id:
        payload["session_id"] = session_id
    if template_id:
        payload["template_id"] = template_id

    with client.stream("POST", "/api/v1/research", json=payload) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        for line in response.iter_lines():
            if not line or not line.startswith("data: "):
                continue
            event = json.loads(line[6:])
            events.append(event)

    return events


def test_research_templates_endpoint_returns_wave15_catalog() -> None:
    response = client.get("/api/v1/research/templates")
    assert response.status_code == 200
    payload = response.json()

    assert payload["count"] == 4
    template_ids = [item["id"] for item in payload["templates"]]
    assert template_ids == [
        "macro_outlook",
        "event_probability_interpretation",
        "ticker_macro_framing",
        "thesis_change_compare",
    ]


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
        "signal_conflicts": brief_payload.get("signal_conflicts", []),
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
    assert brief.template_id == "macro_outlook"
    assert complete["template_id"] == "macro_outlook"
    assert len(brief.sources) >= 3
    assert brief.provenance_summary is not None
    assert brief.snapshot_summary is not None
    assert all(source.provenance is not None for source in brief.sources)
    assert all(source.provenance and source.provenance.snapshot is not None for source in brief.sources)
    assert all(
        source.provenance and source.provenance.state_label in {"fixture", "cached", "live", "derived", "unknown"}
        for source in brief.sources
    )
    assert isinstance(brief.snapshot_summary.get("state_label_counts"), dict)
    assert isinstance(brief.snapshot_summary.get("timing_summary"), dict)
    assert isinstance(complete.get("provenance"), dict)
    assert isinstance(complete.get("snapshot"), dict)
    assert isinstance(complete.get("evaluation"), dict)
    assert complete["evaluation"]["version"] == "phase-7"
    assert complete["evaluation"]["passed"] is True
    check_ids = {check["check_id"] for check in complete["evaluation"]["checks"]}
    assert {
        "snapshot_metadata_complete",
        "snapshot_source_consistency",
        "cache_lineage_visibility",
        "bundle_snapshot_provenance_ready",
        "freshness_policy_compliance",
    }.issubset(check_ids)


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


def test_research_brief_emits_claim_navigation_and_conflicts() -> None:
    events = _collect_events(
        question="What does the current yield curve shape imply for equities over the next 6 months?",
        session_id="phase3-claim-nav-session",
    )

    complete = events[-1]
    assert complete["type"] == "complete"

    brief = ResearchBrief.model_validate(complete["brief"])
    claim_ids = [
        *[item.claim_id for item in brief.bull_case],
        *[item.claim_id for item in brief.bear_case],
        *[item.claim_id for item in brief.key_risks],
    ]
    assert len(claim_ids) == len(set(claim_ids))

    referenced_claims = {
        claim_ref
        for source in brief.sources
        for claim_ref in source.claim_refs
    }
    assert set(claim_ids).issubset(referenced_claims)

    assert len(brief.signal_conflicts) >= 1
    known_sources = {f"{source.type}:{source.id}" for source in brief.sources}
    for conflict in brief.signal_conflicts:
        assert len(conflict.claim_refs) >= 2
        assert set(conflict.claim_refs).issubset(set(claim_ids))
        assert set(conflict.source_refs).issubset(known_sources)


def test_research_demo_output_is_deterministic_for_same_question() -> None:
    events_a = _collect_events(
        question="Frame AAPL versus macro conditions for a cautious equity book.",
        session_id="phase2-determinism-a",
        template_id="ticker_macro_framing",
    )
    events_b = _collect_events(
        question="Frame AAPL versus macro conditions for a cautious equity book.",
        session_id="phase2-determinism-b",
        template_id="ticker_macro_framing",
    )

    brief_a = events_a[-1]["brief"]
    brief_b = events_b[-1]["brief"]
    eval_a = events_a[-1]["evaluation"]
    eval_b = events_b[-1]["evaluation"]

    assert _brief_signature(brief_a) == _brief_signature(brief_b)
    assert eval_a["deterministic_signature"] == eval_b["deterministic_signature"]
    assert brief_a.get("snapshot_summary") == brief_b.get("snapshot_summary")
    assert brief_a.get("template_id") == "ticker_macro_framing"
    assert brief_b.get("template_id") == "ticker_macro_framing"


def test_research_template_selection_changes_brief_shape() -> None:
    events = _collect_events(
        question="Compare my old thesis with the latest macro evidence.",
        session_id="phase15-template-thesis-delta",
        template_id="thesis_change_compare",
    )
    complete = events[-1]
    brief = ResearchBrief.model_validate(complete["brief"])

    assert brief.template_id == "thesis_change_compare"
    assert brief.template_title == "Compare old vs new thesis"
    assert brief.query_class == "macro_outlook"
    assert "prior thesis" in (brief.follow_up_context or "").lower() or brief.follow_up_context is None
