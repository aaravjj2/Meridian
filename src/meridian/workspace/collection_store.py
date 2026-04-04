from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from meridian.normalisation.schemas import (
    ResearchCollection,
    ResearchCollectionSummary,
    CreateCollectionRequest,
    UpdateCollectionRequest,
    AddSessionToCollectionRequest,
)
from meridian.settings import ROOT_DIR


def _default_collection_dir() -> Path:
    configured = os.getenv("MERIDIAN_COLLECTION_STORE_DIR", "").strip()
    if configured:
        path = Path(configured)
        if not path.is_absolute():
            path = ROOT_DIR / path
        return path
    return ROOT_DIR / "data" / "processed" / "collections"


def _iso_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _hash_canonical_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class ResearchCollectionStore:
    def __init__(self, root_dir: Path | None = None) -> None:
        self.root_dir = root_dir or _default_collection_dir()
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _path_for_id(self, collection_id: str) -> Path:
        return self.root_dir / f"{collection_id}.json"

    def _compute_signature(self, collection: ResearchCollection) -> str:
        payload = {
            "title": collection.title,
            "summary": collection.summary,
            "notes": collection.notes,
            "session_ids": collection.session_ids,
        }
        return _hash_canonical_payload(payload)

    def _write_record(self, collection: ResearchCollection) -> None:
        self._path_for_id(collection.id).write_text(
            collection.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )

    def _load_record(self, path: Path) -> ResearchCollection | None:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return ResearchCollection.model_validate(payload)
        except Exception:
            return None

    def _all_records(self) -> list[ResearchCollection]:
        records: list[ResearchCollection] = []
        for path in sorted(self.root_dir.glob("*.json")):
            record = self._load_record(path)
            if record is not None:
                records.append(record)
        records.sort(key=lambda item: item.updated_at, reverse=True)
        return records

    def _build_summary(self, collection: ResearchCollection) -> ResearchCollectionSummary:
        return ResearchCollectionSummary(
            id=collection.id,
            title=collection.title,
            summary=collection.summary,
            session_count=len(collection.session_ids),
            created_at=collection.created_at,
            updated_at=collection.updated_at,
            collection_signature=collection.collection_signature,
        )

    def create(self, request: CreateCollectionRequest) -> ResearchCollection:
        timestamp = _iso_now()
        collection_id = f"coll-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"

        collection = ResearchCollection(
            id=collection_id,
            title=request.title.strip(),
            summary=request.summary.strip() if request.summary else None,
            notes=request.notes.strip() if request.notes else None,
            session_ids=[],
            created_at=timestamp,
            updated_at=timestamp,
            collection_signature="",  # Will be set below
        )
        collection.collection_signature = self._compute_signature(collection)
        self._write_record(collection)
        return collection

    def list_collections(self) -> list[ResearchCollectionSummary]:
        return [self._build_summary(record) for record in self._all_records()]

    def get(self, collection_id: str) -> ResearchCollection | None:
        path = self._path_for_id(collection_id)
        if not path.exists():
            return None
        return self._load_record(path)

    def update(self, collection_id: str, request: UpdateCollectionRequest) -> ResearchCollection | None:
        collection = self.get(collection_id)
        if collection is None:
            return None

        if request.title is not None:
            collection.title = request.title.strip()
        if request.summary is not None:
            collection.summary = request.summary.strip() or None
        if request.notes is not None:
            collection.notes = request.notes.strip() or None

        collection.updated_at = _iso_now()
        collection.collection_signature = self._compute_signature(collection)
        self._write_record(collection)
        return collection

    def delete(self, collection_id: str) -> bool:
        path = self._path_for_id(collection_id)
        if not path.exists():
            return False
        path.unlink()
        return True

    def add_session(self, collection_id: str, request: AddSessionToCollectionRequest) -> ResearchCollection | None:
        collection = self.get(collection_id)
        if collection is None:
            return None

        if request.session_id in collection.session_ids:
            return collection  # Already in collection

        updated_sessions = list(collection.session_ids)
        if request.position is not None and 0 <= request.position <= len(updated_sessions):
            updated_sessions.insert(request.position, request.session_id)
        else:
            updated_sessions.append(request.session_id)

        collection.session_ids = updated_sessions
        collection.updated_at = _iso_now()
        collection.collection_signature = self._compute_signature(collection)
        self._write_record(collection)
        return collection

    def remove_session(self, collection_id: str, session_id: str) -> ResearchCollection | None:
        collection = self.get(collection_id)
        if collection is None:
            return None

        if session_id not in collection.session_ids:
            return collection  # Not in collection

        collection.session_ids = [sid for sid in collection.session_ids if sid != session_id]
        collection.updated_at = _iso_now()
        collection.collection_signature = self._compute_signature(collection)
        self._write_record(collection)
        return collection

    def reorder_sessions(self, collection_id: str, session_ids: list[str]) -> ResearchCollection | None:
        collection = self.get(collection_id)
        if collection is None:
            return None

        # Verify all session IDs are in the current collection
        current_set = set(collection.session_ids)
        requested_set = set(session_ids)
        if current_set != requested_set:
            raise ValueError("Cannot reorder: session IDs don't match collection contents")

        collection.session_ids = session_ids
        collection.updated_at = _iso_now()
        collection.collection_signature = self._compute_signature(collection)
        self._write_record(collection)
        return collection


_STORE: ResearchCollectionStore | None = None


def get_collection_store() -> ResearchCollectionStore:
    global _STORE
    root_dir = _default_collection_dir()
    if _STORE is None or _STORE.root_dir != root_dir:
        _STORE = ResearchCollectionStore(root_dir=root_dir)
    return _STORE
