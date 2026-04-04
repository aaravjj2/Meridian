from __future__ import annotations

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from meridian.workspace import collection_store as collection_store_module


client = TestClient(app)


@pytest.fixture(autouse=True)
def _isolated_collection_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    store_path = tmp_path / "collections"
    monkeypatch.setenv("MERIDIAN_COLLECTION_STORE_DIR", str(store_path))
    collection_store_module._STORE = None
    yield
    collection_store_module._STORE = None


def test_collection_create_and_list():
    # Create a collection
    response = client.post(
        "/api/v1/collections",
        json={"title": "Market Research 2026", "summary": "Q1 analysis"}
    )
    assert response.status_code == 200
    collection = response.json()
    assert collection["id"].startswith("coll-")
    assert collection["title"] == "Market Research 2026"
    assert collection["summary"] == "Q1 analysis"
    assert collection["session_ids"] == []

    # List collections
    response = client.get("/api/v1/collections")
    assert response.status_code == 200
    listing = response.json()
    assert listing["count"] == 1
    assert listing["collections"][0]["id"] == collection["id"]
    assert listing["collections"][0]["session_count"] == 0


def test_collection_get_update_delete():
    # Create
    create_response = client.post(
        "/api/v1/collections",
        json={"title": "Test Collection"}
    )
    collection_id = create_response.json()["id"]

    # Get
    response = client.get(f"/api/v1/collections/{collection_id}")
    assert response.status_code == 200
    collection = response.json()
    assert collection["title"] == "Test Collection"

    # Update
    response = client.patch(
        f"/api/v1/collections/{collection_id}",
        json={"title": "Updated Title", "notes": "Some notes"}
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["title"] == "Updated Title"
    assert updated["notes"] == "Some notes"

    # Delete
    response = client.delete(f"/api/v1/collections/{collection_id}")
    assert response.status_code == 200
    assert response.json()["deleted"] is True

    # Verify deleted
    response = client.get(f"/api/v1/collections/{collection_id}")
    assert response.status_code == 404


def test_collection_add_remove_reorder_sessions():
    # Create collection
    create_response = client.post(
        "/api/v1/collections",
        json={"title": "Session Collection"}
    )
    collection_id = create_response.json()["id"]

    # Add sessions
    response = client.post(
        f"/api/v1/collections/{collection_id}/sessions",
        json={"session_id": "rs-test-session-1"}
    )
    assert response.status_code == 200
    collection = response.json()
    assert "rs-test-session-1" in collection["session_ids"]

    response = client.post(
        f"/api/v1/collections/{collection_id}/sessions",
        json={"session_id": "rs-test-session-2", "position": 0}
    )
    assert response.status_code == 200
    collection = response.json()
    assert collection["session_ids"] == ["rs-test-session-2", "rs-test-session-1"]

    # Remove session
    response = client.delete(
        f"/api/v1/collections/{collection_id}/sessions/rs-test-session-1"
    )
    assert response.status_code == 200
    collection = response.json()
    assert collection["session_ids"] == ["rs-test-session-2"]

    # Reorder
    response = client.put(
        f"/api/v1/collections/{collection_id}/sessions/reorder",
        json={"session_ids": ["rs-test-session-2"]}
    )
    assert response.status_code == 200
