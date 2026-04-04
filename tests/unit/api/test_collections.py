from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.routers import research as research_router
from meridian.normalisation.schemas import ResearchCollection
from meridian.workspace import collection_store as collection_store_module
from meridian.workspace import session_store as session_store_module


client = TestClient(app)


@pytest.fixture(autouse=True)
def _isolated_workspace_and_collection_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    collection_path = tmp_path / "collections"
    session_path = tmp_path / "research_sessions"
    monkeypatch.setenv("MERIDIAN_COLLECTION_STORE_DIR", str(collection_path))
    monkeypatch.setenv("MERIDIAN_SESSION_STORE_DIR", str(session_path))

    collection_store_module._STORE = None
    session_store_module._STORE = None
    research_router.SESSION_CONTEXT.clear()
    yield
    collection_store_module._STORE = None
    session_store_module._STORE = None
    research_router.SESSION_CONTEXT.clear()


def _collect_events(question: str, session_id: str) -> list[dict]:
    events: list[dict] = []
    with client.stream(
        "POST",
        "/api/v1/research",
        json={"question": question, "mode": "demo", "session_id": session_id},
    ) as response:
        assert response.status_code == 200
        for line in response.iter_lines():
            if not line or not line.startswith("data: "):
                continue
            events.append(json.loads(line[6:]))
    return events


def _save_session(question: str, session_id: str) -> dict:
    events = _collect_events(question=question, session_id=session_id)
    complete = events[-1]
    response = client.post(
        "/api/v1/research/sessions",
        json={
            "question": question,
            "mode": "demo",
            "session_id": session_id,
            "brief": complete["brief"],
            "trace_events": events,
            "evidence_state": {
                "active_claim_id": complete["brief"]["bull_case"][0]["claim_id"],
                "expanded_source_id": f"{complete['brief']['sources'][0]['type']}:{complete['brief']['sources'][0]['id']}",
            },
        },
    )
    assert response.status_code == 200
    return response.json()


def test_collection_schema_validation_rejects_invalid_values() -> None:
    with pytest.raises(Exception):
        ResearchCollection(
            id="bad-collection-id",
            title="Valid title",
            summary=None,
            notes=None,
            session_ids=[],
            created_at="2026-04-04T00:00:00Z",
            updated_at="2026-04-04T00:00:00Z",
            collection_signature="sig",
        )

    with pytest.raises(Exception):
        ResearchCollection(
            id="coll-20260404000000-deadbeef",
            title="   ",
            summary=None,
            notes=None,
            session_ids=[],
            created_at="2026-04-04T00:00:00Z",
            updated_at="2026-04-04T00:00:00Z",
            collection_signature="sig",
        )


def test_collection_create_list_get_update_delete() -> None:
    created_response = client.post(
        "/api/v1/collections",
        json={
            "title": "Market Research 2026",
            "summary": "Q1 analysis",
            "notes": "starting notebook",
        },
    )
    assert created_response.status_code == 200
    created_payload = created_response.json()
    assert "collection" in created_payload
    assert created_payload["timeline"] == []
    assert created_payload["missing_session_count"] == 0

    collection = created_payload["collection"]
    assert collection["id"].startswith("coll-")
    assert collection["title"] == "Market Research 2026"
    assert collection["summary"] == "Q1 analysis"
    assert collection["notes"] == "starting notebook"
    assert collection["session_ids"] == []
    assert collection["collection_signature"]

    list_response = client.get("/api/v1/collections")
    assert list_response.status_code == 200
    listing = list_response.json()
    assert listing["count"] == 1
    assert listing["collections"][0]["id"] == collection["id"]
    assert listing["collections"][0]["session_count"] == 0

    get_response = client.get(f"/api/v1/collections/{collection['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["collection"]["title"] == "Market Research 2026"

    update_response = client.patch(
        f"/api/v1/collections/{collection['id']}",
        json={"title": "Updated Title", "summary": "Updated summary", "notes": "Updated notes"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()["collection"]
    assert updated["title"] == "Updated Title"
    assert updated["summary"] == "Updated summary"
    assert updated["notes"] == "Updated notes"

    delete_response = client.delete(f"/api/v1/collections/{collection['id']}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True

    missing_response = client.get(f"/api/v1/collections/{collection['id']}")
    assert missing_response.status_code == 404


def test_collection_add_remove_reorder_and_ordered_timeline() -> None:
    saved_a = _save_session(
        question="What does the current yield curve shape imply for equities?",
        session_id="wave12-coll-thread-a",
    )
    saved_b = _save_session(
        question="Continue from this thread with an event probability framing.",
        session_id="wave12-coll-thread-b",
    )

    created = client.post("/api/v1/collections", json={"title": "Session Collection"})
    assert created.status_code == 200
    collection_id = created.json()["collection"]["id"]

    add_a = client.post(
        f"/api/v1/collections/{collection_id}/sessions",
        json={"session_id": saved_a["id"]},
    )
    assert add_a.status_code == 200

    add_b_at_front = client.post(
        f"/api/v1/collections/{collection_id}/sessions",
        json={"session_id": saved_b["id"], "position": 0},
    )
    assert add_b_at_front.status_code == 200
    detail = add_b_at_front.json()
    assert detail["collection"]["session_ids"] == [saved_b["id"], saved_a["id"]]
    assert detail["timeline"][0]["session_id"] == saved_b["id"]
    assert detail["timeline"][1]["session_id"] == saved_a["id"]
    assert detail["timeline"][0]["exists"] is True
    assert detail["timeline"][0]["question"]
    assert detail["timeline"][0]["query_class"] in {"macro_outlook", "event_probability", "ticker_macro"}

    invalid_reorder = client.put(
        f"/api/v1/collections/{collection_id}/sessions/reorder",
        json={"session_ids": [saved_a["id"]]},
    )
    assert invalid_reorder.status_code == 400

    remove_a = client.delete(f"/api/v1/collections/{collection_id}/sessions/{saved_a['id']}")
    assert remove_a.status_code == 200
    assert remove_a.json()["collection"]["session_ids"] == [saved_b["id"]]

    reorder_single = client.put(
        f"/api/v1/collections/{collection_id}/sessions/reorder",
        json={"session_ids": [saved_b["id"]]},
    )
    assert reorder_single.status_code == 200
    assert reorder_single.json()["collection"]["session_ids"] == [saved_b["id"]]


def test_collection_signature_is_deterministic_for_identical_ordered_contents() -> None:
    saved_a = _save_session(
        question="Baseline macro notebook session.",
        session_id="wave12-determinism-a",
    )
    saved_b = _save_session(
        question="Follow-up notebook session.",
        session_id="wave12-determinism-b",
    )

    created = client.post("/api/v1/collections", json={"title": "Deterministic Notebook"})
    assert created.status_code == 200
    collection_id = created.json()["collection"]["id"]

    add_a = client.post(f"/api/v1/collections/{collection_id}/sessions", json={"session_id": saved_a["id"]})
    assert add_a.status_code == 200
    add_b = client.post(f"/api/v1/collections/{collection_id}/sessions", json={"session_id": saved_b["id"]})
    assert add_b.status_code == 200
    signature_ab = add_b.json()["collection"]["collection_signature"]

    swapped = client.put(
        f"/api/v1/collections/{collection_id}/sessions/reorder",
        json={"session_ids": [saved_b["id"], saved_a["id"]]},
    )
    assert swapped.status_code == 200
    signature_ba = swapped.json()["collection"]["collection_signature"]
    assert signature_ba != signature_ab

    restored = client.put(
        f"/api/v1/collections/{collection_id}/sessions/reorder",
        json={"session_ids": [saved_a["id"], saved_b["id"]]},
    )
    assert restored.status_code == 200
    signature_restored = restored.json()["collection"]["collection_signature"]
    assert signature_restored == signature_ab

    removed = client.delete(f"/api/v1/collections/{collection_id}/sessions/{saved_b['id']}")
    assert removed.status_code == 200
    readded = client.post(f"/api/v1/collections/{collection_id}/sessions", json={"session_id": saved_b["id"]})
    assert readded.status_code == 200
    signature_readded = readded.json()["collection"]["collection_signature"]
    assert signature_readded == signature_ab


def test_collection_reopen_timeline_session_matches_workspace_lookup() -> None:
    saved = _save_session(
        question="Session to reopen from collection timeline.",
        session_id="wave12-reopen-thread",
    )

    created = client.post("/api/v1/collections", json={"title": "Reopen Checks"})
    assert created.status_code == 200
    collection_id = created.json()["collection"]["id"]

    added = client.post(
        f"/api/v1/collections/{collection_id}/sessions",
        json={"session_id": saved["id"]},
    )
    assert added.status_code == 200
    timeline_session_id = added.json()["timeline"][0]["session_id"]

    reopened = client.get(f"/api/v1/research/sessions/{timeline_session_id}")
    assert reopened.status_code == 200
    assert reopened.json()["id"] == saved["id"]
    assert reopened.json()["question"] == saved["question"]

    missing_session_add = client.post(
        f"/api/v1/collections/{collection_id}/sessions",
        json={"session_id": "rs-missing-session"},
    )
    assert missing_session_add.status_code == 404
