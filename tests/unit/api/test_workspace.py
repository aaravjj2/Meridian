from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.routers import research as research_router
from meridian.normalisation.schemas import ResearchBrief
from meridian.workspace import session_store as session_store_module


client = TestClient(app)


@pytest.fixture(autouse=True)
def _isolated_workspace_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    store_path = tmp_path / "research_sessions"
    monkeypatch.setenv("MERIDIAN_SESSION_STORE_DIR", str(store_path))
    session_store_module._STORE = None
    research_router.SESSION_CONTEXT.clear()
    yield
    session_store_module._STORE = None
    research_router.SESSION_CONTEXT.clear()


def _collect_events(question: str, session_id: str | None = None) -> list[dict]:
    events: list[dict] = []
    payload: dict[str, object] = {"question": question, "mode": "demo"}
    if session_id:
        payload["session_id"] = session_id

    with client.stream("POST", "/api/v1/research", json=payload) as response:
        assert response.status_code == 200
        for line in response.iter_lines():
            if not line or not line.startswith("data: "):
                continue
            events.append(json.loads(line[6:]))
    return events


def _save_payload(question: str, session_id: str, events: list[dict], brief: dict) -> dict:
    return {
        "question": question,
        "mode": "demo",
        "session_id": session_id,
        "label": f"label-{session_id}",
        "brief": brief,
        "trace_events": events,
        "evidence_state": {
            "active_claim_id": brief["bull_case"][0]["claim_id"],
            "expanded_source_id": f"{brief['sources'][0]['type']}:{brief['sources'][0]['id']}",
        },
    }


def test_workspace_save_list_get_and_export_roundtrip() -> None:
    question = "What does the current yield curve shape imply for equities over the next 6 months?"
    thread_id = "phase4-workspace-thread"
    events = _collect_events(question=question, session_id=thread_id)
    complete = events[-1]

    save_response = client.post(
        "/api/v1/research/sessions",
        json=_save_payload(question=question, session_id=thread_id, events=events, brief=complete["brief"]),
    )
    assert save_response.status_code == 200

    saved = save_response.json()
    assert saved["id"].startswith("rs-")
    assert saved["mode"] == "demo"
    assert saved["session_id"] == thread_id
    assert saved["canonical_signature"]
    assert saved["brief"]["provenance_summary"]["source_count"] >= 3
    assert saved["brief"]["snapshot_summary"]["snapshot_count"] >= 3
    assert saved["evaluation"]["version"] == "phase-7"
    assert saved["evaluation"]["passed"] is True
    assert any(
        check["check_id"] == "freshness_policy_compliance"
        for check in saved["evaluation"]["checks"]
    )

    listed = client.get("/api/v1/research/sessions")
    assert listed.status_code == 200
    listing = listed.json()
    assert listing["count"] == 1
    assert listing["sessions"][0]["id"] == saved["id"]
    assert listing["sessions"][0]["evaluation_passed"] is True
    assert isinstance(listing["sessions"][0]["snapshot_kind_counts"], dict)
    assert listing["sessions"][0]["snapshot_signature"]

    loaded = client.get(f"/api/v1/research/sessions/{saved['id']}")
    assert loaded.status_code == 200
    loaded_payload = loaded.json()
    brief = ResearchBrief.model_validate(loaded_payload["brief"])
    assert brief.thesis
    assert len(loaded_payload["trace_events"]) >= 5
    assert loaded_payload["evidence_state"]["active_claim_id"]

    exported_json = client.get(f"/api/v1/research/sessions/{saved['id']}/export", params={"format": "json"})
    assert exported_json.status_code == 200
    assert "application/json" in exported_json.headers["content-type"]
    json_payload = exported_json.json()
    assert json_payload["question"] == question
    assert json_payload["brief"]["thesis"]
    assert json_payload["brief"]["signal_conflicts"]
    assert json_payload["trace_events"]

    exported_md = client.get(f"/api/v1/research/sessions/{saved['id']}/export", params={"format": "markdown"})
    assert exported_md.status_code == 200
    assert "text/markdown" in exported_md.headers["content-type"]
    markdown = exported_md.text
    assert "## Thesis" in markdown
    assert "## Signal Conflicts" in markdown
    assert "## Trace Payload" in markdown


def test_workspace_saved_session_signature_is_deterministic_for_demo_runs() -> None:
    question = "Frame AAPL versus macro conditions for a cautious equity book."

    events_a = _collect_events(question=question, session_id="phase4-det-thread-a")
    complete_a = events_a[-1]
    saved_a = client.post(
        "/api/v1/research/sessions",
        json=_save_payload(
            question=question,
            session_id="phase4-det-thread-a",
            events=events_a,
            brief=complete_a["brief"],
        ),
    )
    assert saved_a.status_code == 200

    events_b = _collect_events(question=question, session_id="phase4-det-thread-b")
    complete_b = events_b[-1]
    saved_b = client.post(
        "/api/v1/research/sessions",
        json=_save_payload(
            question=question,
            session_id="phase4-det-thread-b",
            events=events_b,
            brief=complete_b["brief"],
        ),
    )
    assert saved_b.status_code == 200

    assert saved_a.json()["canonical_signature"] == saved_b.json()["canonical_signature"]
    assert (
        saved_a.json()["evaluation"]["deterministic_signature"]
        == saved_b.json()["evaluation"]["deterministic_signature"]
    )
    assert saved_a.json()["brief"]["snapshot_summary"] == saved_b.json()["brief"]["snapshot_summary"]

    bundle_a = client.get(f"/api/v1/research/sessions/{saved_a.json()['id']}/bundle")
    bundle_b = client.get(f"/api/v1/research/sessions/{saved_b.json()['id']}/bundle")
    assert bundle_a.status_code == 200
    assert bundle_b.status_code == 200
    assert (
        bundle_a.json()["snapshot_provenance"]["signature_sha256"]
        == bundle_b.json()["snapshot_provenance"]["signature_sha256"]
    )

    compare_a = client.get(
        "/api/v1/research/sessions/compare",
        params={"left_id": saved_a.json()["id"], "right_id": saved_b.json()["id"]},
    )
    compare_b = client.get(
        "/api/v1/research/sessions/compare",
        params={"left_id": saved_a.json()["id"], "right_id": saved_b.json()["id"]},
    )
    assert compare_a.status_code == 200
    assert compare_b.status_code == 200
    drift_a = compare_a.json()["snapshot_drift"]
    drift_b = compare_b.json()["snapshot_drift"]
    assert drift_a["drift_signature"] == drift_b["drift_signature"]
    assert drift_a["snapshot_signature_changed"] is False
    assert drift_a["evaluation_signature_changed"] is False
    assert drift_a["source_set_changed"] is False
    assert drift_a["snapshot_ids_changed"] == []
    assert drift_a["freshness_changed"] == []
    assert compare_a.json()["conflict_diffs"]["drift_signature"] == compare_b.json()["conflict_diffs"]["drift_signature"]
    assert compare_a.json()["summary"]["worsened_conflict_count"] == 0

    recapture_first = client.post(f"/api/v1/research/sessions/{saved_a.json()['id']}/recapture")
    recapture_second = client.post(f"/api/v1/research/sessions/{saved_a.json()['id']}/recapture")
    assert recapture_first.status_code == 200
    assert recapture_second.status_code == 200

    recapture_one = recapture_first.json()
    recapture_two = recapture_second.json()
    assert recapture_one["saved"]["id"] != saved_a.json()["id"]
    assert recapture_one["saved"]["id"] != recapture_two["saved"]["id"]
    assert recapture_one["lineage"]["source_session_id"] == saved_a.json()["id"]
    assert recapture_one["lineage"]["recapture_mode"] == "demo_pseudo_refresh"
    assert recapture_one["lineage"]["snapshot_id_changes"] >= 1
    assert recapture_one["lineage"]["before_snapshot_signature"] == recapture_two["lineage"]["before_snapshot_signature"]
    assert recapture_one["lineage"]["after_snapshot_signature"] == recapture_two["lineage"]["after_snapshot_signature"]


def test_workspace_continue_from_saved_restores_followup_context() -> None:
    initial_question = "Give me a macro outlook for the next two quarters."
    follow_up = "How should I interpret the event probability if inflation re-accelerates?"
    thread_id = "phase4-continue-thread"

    initial_events = _collect_events(question=initial_question, session_id=thread_id)
    initial_complete = initial_events[-1]

    saved_response = client.post(
        "/api/v1/research/sessions",
        json=_save_payload(
            question=initial_question,
            session_id=thread_id,
            events=initial_events,
            brief=initial_complete["brief"],
        ),
    )
    assert saved_response.status_code == 200

    # Simulate server restart by clearing in-memory continuity cache.
    research_router.SESSION_CONTEXT.clear()

    continued_events = _collect_events(question=follow_up, session_id=thread_id)
    continued_complete = continued_events[-1]

    assert continued_complete["followup"] is True
    assert continued_complete["session_context_used"] is True
    continued_brief = ResearchBrief.model_validate(continued_complete["brief"])
    assert continued_brief.follow_up_context is not None
    assert initial_question.lower() in continued_brief.follow_up_context.lower()


def test_workspace_thread_timeline_returns_ordered_thesis_evolution() -> None:
    thread_id = "wave13-thread-timeline"

    first_question = "Set baseline macro thesis for this thread."
    second_question = "Evolve the same thread into event probability framing."

    first_events = _collect_events(question=first_question, session_id=thread_id)
    second_events = _collect_events(question=second_question, session_id=thread_id)

    first_saved_response = client.post(
        "/api/v1/research/sessions",
        json=_save_payload(
            question=first_question,
            session_id=thread_id,
            events=first_events,
            brief=first_events[-1]["brief"],
        ),
    )
    second_saved_response = client.post(
        "/api/v1/research/sessions",
        json=_save_payload(
            question=second_question,
            session_id=thread_id,
            events=second_events,
            brief=second_events[-1]["brief"],
        ),
    )
    assert first_saved_response.status_code == 200
    assert second_saved_response.status_code == 200

    first_saved = first_saved_response.json()
    second_saved = second_saved_response.json()

    timeline_response = client.get(f"/api/v1/research/sessions/{second_saved['id']}/timeline")
    assert timeline_response.status_code == 200
    timeline_payload = timeline_response.json()

    assert timeline_payload["thread_session_id"] == thread_id
    assert timeline_payload["timeline_signature"]
    assert len(timeline_payload["timeline"]) == 2
    assert [item["session_id"] for item in timeline_payload["timeline"]] == [
        first_saved["id"],
        second_saved["id"],
    ]

    first_entry = timeline_payload["timeline"][0]
    second_entry = timeline_payload["timeline"][1]

    assert first_entry["thesis_state"]["thesis"]
    assert first_entry["thesis_state"]["claim_count"] >= 1
    assert first_entry["thesis_delta"]["previous_session_id"] is None
    assert first_entry["thesis_delta"]["delta_signature"]

    assert second_entry["thesis_state"]["thesis"]
    assert second_entry["thesis_delta"]["previous_session_id"] == first_saved["id"]
    assert second_entry["thesis_delta"]["delta_signature"]
    assert isinstance(second_entry["thesis_delta"]["thesis_changed"], bool)
    assert isinstance(second_entry["thesis_delta"]["confidence_changed"], bool)
    assert isinstance(second_entry["thesis_delta"]["claims_changed"], bool)
    assert isinstance(second_entry["thesis_delta"]["freshness_policy_changed"], bool)
    assert isinstance(second_entry["thesis_delta"]["conflicts_changed"], bool)
    assert isinstance(second_entry["thesis_delta"]["evaluation_changed"], bool)

    timeline_again = client.get(f"/api/v1/research/sessions/{second_saved['id']}/timeline")
    assert timeline_again.status_code == 200
    assert timeline_again.json()["timeline_signature"] == timeline_payload["timeline_signature"]


def test_workspace_phase5_management_compare_bundle_and_integrity() -> None:
    first_question = "Assess recession odds over the next six months."
    second_question = "Update the same thread with an event-probability framing."

    first_events = _collect_events(question=first_question, session_id="phase5-thread-one")
    second_events = _collect_events(question=second_question, session_id="phase5-thread-two")
    first_complete = first_events[-1]
    second_complete = second_events[-1]

    first_saved = client.post(
        "/api/v1/research/sessions",
        json=_save_payload(
            question=first_question,
            session_id="phase5-thread-one",
            events=first_events,
            brief=first_complete["brief"],
        ),
    )
    second_saved = client.post(
        "/api/v1/research/sessions",
        json=_save_payload(
            question=second_question,
            session_id="phase5-thread-two",
            events=second_events,
            brief=second_complete["brief"],
        ),
    )
    assert first_saved.status_code == 200
    assert second_saved.status_code == 200

    first_id = first_saved.json()["id"]
    second_id = second_saved.json()["id"]

    renamed = client.patch(
        f"/api/v1/research/sessions/{first_id}/rename",
        json={"label": "phase5-renamed-session"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["label"] == "phase5-renamed-session"

    archived = client.patch(
        f"/api/v1/research/sessions/{first_id}/archive",
        json={"archived": True},
    )
    assert archived.status_code == 200
    assert archived.json()["archived"] is True
    assert archived.json()["archived_at"]

    list_active = client.get("/api/v1/research/sessions")
    assert list_active.status_code == 200
    assert list_active.json()["count"] == 1
    assert list_active.json()["sessions"][0]["id"] == second_id

    list_all = client.get("/api/v1/research/sessions", params={"include_archived": "true"})
    assert list_all.status_code == 200
    assert list_all.json()["count"] == 2

    list_search = client.get(
        "/api/v1/research/sessions",
        params={"include_archived": "true", "search": "renamed"},
    )
    assert list_search.status_code == 200
    assert list_search.json()["count"] == 1
    assert list_search.json()["sessions"][0]["id"] == first_id

    compare = client.get(
        "/api/v1/research/sessions/compare",
        params={"left_id": first_id, "right_id": second_id},
    )
    assert compare.status_code == 200
    comparison_payload = compare.json()
    assert comparison_payload["left_id"] == first_id
    assert comparison_payload["right_id"] == second_id
    assert "summary" in comparison_payload
    assert "trace_diffs" in comparison_payload
    assert "snapshot_drift" in comparison_payload
    assert "conflict_diffs" in comparison_payload
    assert comparison_payload["snapshot_drift"]["drift_signature"]
    assert comparison_payload["conflict_diffs"]["drift_signature"]
    assert isinstance(comparison_payload["snapshot_drift"]["snapshot_ids_changed"], list)
    assert isinstance(comparison_payload["snapshot_drift"]["freshness_changed"], list)
    assert isinstance(comparison_payload["snapshot_drift"]["source_set_changed"], bool)
    assert isinstance(comparison_payload["snapshot_drift"]["evaluation_signature_changed"], bool)
    assert isinstance(comparison_payload["conflict_diffs"]["resolved"], list)
    assert isinstance(comparison_payload["conflict_diffs"]["unchanged"], list)
    assert isinstance(comparison_payload["conflict_diffs"]["worsened"], list)

    recaptured = client.post(f"/api/v1/research/sessions/{first_id}/recapture")
    assert recaptured.status_code == 200
    recapture_payload = recaptured.json()
    assert recapture_payload["saved"]["id"] != first_id
    assert recapture_payload["lineage"]["source_session_id"] == first_id
    assert recapture_payload["lineage"]["recaptured_session_id"] == recapture_payload["saved"]["id"]
    assert recapture_payload["lineage"]["snapshot_id_changes"] >= 1
    assert recapture_payload["lineage"]["transition_count"] >= 1

    integrity_single = client.get(f"/api/v1/research/sessions/{first_id}/integrity")
    assert integrity_single.status_code == 200
    integrity_payload = integrity_single.json()
    assert integrity_payload["id"] == first_id
    assert integrity_payload["signature_valid"] is True
    assert integrity_payload["provenance_complete"] is True
    assert integrity_payload["freshness_valid"] is True
    assert integrity_payload["freshness_policy_valid"] is True
    assert integrity_payload["freshness_policy_violation_count"] == 0
    assert integrity_payload["snapshot_complete"] is True
    assert integrity_payload["snapshot_consistent"] is True
    assert integrity_payload["snapshot_summary_present"] is True
    assert integrity_payload["snapshot_checksum_complete"] is True
    assert integrity_payload["bundle_snapshot_signature"]
    assert integrity_payload["evaluation_present"] is True
    assert integrity_payload["evaluation_valid"] is True
    assert integrity_payload["issues"] == []

    integrity_all = client.get("/api/v1/research/sessions/integrity", params={"include_archived": "true"})
    assert integrity_all.status_code == 200
    assert integrity_all.json()["count"] == 3
    assert integrity_all.json()["issue_count"] == 0

    bundle_response = client.get(f"/api/v1/research/sessions/{first_id}/bundle")
    assert bundle_response.status_code == 200
    assert "application/json" in bundle_response.headers["content-type"]
    bundle_payload = bundle_response.json()
    assert bundle_payload["bundle_version"] == "phase-7"
    assert bundle_payload["session"]["id"] == first_id
    assert bundle_payload["integrity"]["signature_valid"] is True
    assert bundle_payload["evaluation"]["version"] == "phase-7"
    assert bundle_payload["snapshot_provenance"]["summary"]["snapshot_count"] >= 1
    assert bundle_payload["snapshot_provenance"]["signature_sha256"]

    deleted = client.delete(f"/api/v1/research/sessions/{first_id}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True

    missing = client.get(f"/api/v1/research/sessions/{first_id}")
    assert missing.status_code == 404
