from __future__ import annotations

import hashlib
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from meridian.normalisation.schemas import (
    AddSessionToCollectionRequest,
    CollectionBundleExportV2,
    CreateCollectionRequest,
    ReorderCollectionSessionsRequest,
    ResearchCollection,
    ResearchCollectionDetail,
    ResearchCollectionSummary,
    UpdateCollectionRequest,
)
from meridian.workspace.collection_store import get_collection_store
from meridian.workspace.session_store import get_session_store


router = APIRouter(tags=["collections"])


class CollectionListResponse(BaseModel):
    collections: list[ResearchCollectionSummary]
    count: int


def _hash_value_payload(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_file_size(payload: object) -> int:
    return len((json.dumps(payload, indent=2) + "\n").encode("utf-8"))


def _collection_report_markdown(detail: ResearchCollectionDetail) -> str:
    lines: list[str] = [
        f"# Meridian Collection {detail.collection.id}",
        "",
        "## Metadata",
        f"- Title: {detail.collection.title}",
        f"- Summary: {detail.collection.summary or 'none'}",
        f"- Notes: {detail.collection.notes or 'none'}",
        f"- Session count: {len(detail.collection.session_ids)}",
        f"- Missing sessions: {detail.missing_session_count}",
        f"- Collection signature: {detail.collection.collection_signature}",
        f"- Timeline signature: {detail.timeline_signature}",
        "",
        "## Timeline",
    ]

    if not detail.timeline:
        lines.append("- No sessions in this collection yet.")
    else:
        for idx, entry in enumerate(detail.timeline):
            label = entry.label or entry.question or entry.session_id
            lines.append(
                f"- [{idx + 1}] {label} | id={entry.session_id} | exists={entry.exists} | query_class={entry.query_class or 'unknown'}"
            )

    return "\n".join(lines) + "\n"


def _collection_bundle_payload(collection: ResearchCollection) -> dict[str, object]:
    detail = _detail_from_collection(collection)
    session_store = get_session_store()

    collection_json = detail.collection.model_dump(exclude_none=True)
    timeline_json: dict[str, object] = {
        "collection_id": detail.collection.id,
        "timeline_signature": detail.timeline_signature,
        "missing_session_count": detail.missing_session_count,
        "timeline": [item.model_dump(exclude_none=True) for item in detail.timeline],
    }

    session_rows: list[dict[str, object]] = []
    for entry in detail.timeline:
        saved = session_store.get(entry.session_id)
        if saved is None:
            session_rows.append(
                {
                    "id": entry.session_id,
                    "exists": False,
                }
            )
            continue
        integrity = session_store.verify_integrity(saved.id)
        session_rows.append(
            {
                "id": saved.id,
                "exists": True,
                "question": saved.question,
                "label": saved.label,
                "thread_session_id": saved.session_id,
                "query_class": saved.query_class,
                "saved_at": saved.saved_at,
                "canonical_signature": saved.canonical_signature,
                "evaluation_signature": (
                    saved.evaluation.deterministic_signature if saved.evaluation else None
                ),
                "snapshot_signature": (
                    integrity.bundle_snapshot_signature if integrity else None
                ),
            }
        )

    compare_pairs: list[dict[str, object]] = []
    existing_ids = [entry.session_id for entry in detail.timeline if entry.exists]
    for idx in range(1, len(existing_ids)):
        comparison = session_store.compare(left_id=existing_ids[idx - 1], right_id=existing_ids[idx])
        if comparison is None:
            continue
        compare_pairs.append(comparison.model_dump(exclude_none=True))

    compare_json: dict[str, object] = {
        "pair_count": len(compare_pairs),
        "pairs": compare_pairs,
    }

    report_md = _collection_report_markdown(detail)
    provenance_json: dict[str, object] = {
        "source": "meridian-workspace",
        "app_version": "0.1.0",
        "model": "glm-5.1",
        "bundle_kind": "collection",
        "collection_id": detail.collection.id,
        "collection_signature": detail.collection.collection_signature,
        "timeline_signature": detail.timeline_signature,
        "session_count": len(detail.collection.session_ids),
        "missing_session_count": detail.missing_session_count,
    }

    files: dict[str, object] = {
        "collection.json": collection_json,
        "timeline.json": timeline_json,
        "sessions.json": session_rows,
        "compare.json": compare_json,
        "provenance.json": provenance_json,
        "report.md": report_md,
    }

    inventory: list[dict[str, object]] = []
    section_signatures: dict[str, str] = {}
    for filename, payload in files.items():
        if filename.endswith(".md"):
            encoded = str(payload).encode("utf-8")
            signature = hashlib.sha256(encoded).hexdigest()
            size_bytes = len(encoded)
            media_type = "text/markdown; charset=utf-8"
        else:
            signature = _hash_value_payload(payload)
            size_bytes = _json_file_size(payload)
            media_type = "application/json"
        section_signatures[filename] = signature
        inventory.append(
            {
                "file": filename,
                "media_type": media_type,
                "sha256": signature,
                "size_bytes": size_bytes,
            }
        )

    equality_checks = {
        "collection_signature_present": bool(collection_json.get("collection_signature")),
        "timeline_signature_present": bool(timeline_json.get("timeline_signature")),
        "missing_session_count_zero": detail.missing_session_count == 0,
        "compare_pairs_built": compare_json.get("pair_count", 0) >= 0,
    }

    deterministic_signature = _hash_value_payload(
        {
            "bundle_version": "wave14-v2",
            "bundle_kind": "collection",
            "collection_id": detail.collection.id,
            "section_signatures": section_signatures,
            "equality_checks": equality_checks,
        }
    )

    manifest: dict[str, object] = {
        "schema": "meridian.export_bundle.v2",
        "bundle_kind": "collection",
        "collection_id": detail.collection.id,
        "collection_signature": detail.collection.collection_signature,
        "timeline_signature": detail.timeline_signature,
        "deterministic_signature": deterministic_signature,
        "equality_checks": equality_checks,
        "section_signatures": section_signatures,
        "inventory": inventory,
    }

    bundle = CollectionBundleExportV2.model_validate(
        {
            "bundle_version": "wave14-v2",
            "bundle_kind": "collection",
            "manifest": manifest,
            "files": files,
        }
    )
    return bundle.model_dump(exclude_none=True)


def _detail_from_collection(collection: ResearchCollection) -> ResearchCollectionDetail:
    session_store = get_session_store()
    timeline, missing_session_count, timeline_signature = session_store.build_collection_timeline(
        collection.session_ids
    )

    return ResearchCollectionDetail(
        collection=collection,
        timeline=timeline,
        missing_session_count=missing_session_count,
        timeline_signature=timeline_signature,
    )


@router.post("/collections")
async def create_collection(payload: CreateCollectionRequest) -> dict[str, object]:
    store = get_collection_store()
    collection = store.create(payload)
    return _detail_from_collection(collection).model_dump()


@router.get("/collections")
async def list_collections() -> CollectionListResponse:
    store = get_collection_store()
    summaries = store.list_collections()
    return CollectionListResponse(collections=summaries, count=len(summaries))


@router.get("/collections/{collection_id}")
async def get_collection(collection_id: str) -> dict[str, object]:
    store = get_collection_store()
    collection = store.get(collection_id)
    if collection is None:
        raise HTTPException(status_code=404, detail=f"Collection not found: {collection_id}")
    return _detail_from_collection(collection).model_dump()


@router.patch("/collections/{collection_id}")
async def update_collection(collection_id: str, payload: UpdateCollectionRequest) -> dict[str, object]:
    store = get_collection_store()
    collection = store.update(collection_id, payload)
    if collection is None:
        raise HTTPException(status_code=404, detail=f"Collection not found: {collection_id}")
    return _detail_from_collection(collection).model_dump()


@router.delete("/collections/{collection_id}")
async def delete_collection(collection_id: str) -> dict[str, object]:
    store = get_collection_store()
    deleted = store.delete(collection_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Collection not found: {collection_id}")
    return {"deleted": True, "id": collection_id}


@router.post("/collections/{collection_id}/sessions")
async def add_session_to_collection(
    collection_id: str,
    payload: AddSessionToCollectionRequest,
) -> dict[str, object]:
    store = get_collection_store()
    session_store = get_session_store()
    if session_store.get(payload.session_id) is None:
        raise HTTPException(status_code=404, detail=f"Saved session not found: {payload.session_id}")

    collection = store.add_session(collection_id, payload)
    if collection is None:
        raise HTTPException(status_code=404, detail=f"Collection not found: {collection_id}")
    return _detail_from_collection(collection).model_dump()


@router.delete("/collections/{collection_id}/sessions/{session_id}")
async def remove_session_from_collection(collection_id: str, session_id: str) -> dict[str, object]:
    store = get_collection_store()
    collection = store.remove_session(collection_id, session_id)
    if collection is None:
        raise HTTPException(status_code=404, detail=f"Collection not found: {collection_id}")
    return _detail_from_collection(collection).model_dump()


@router.put("/collections/{collection_id}/sessions/reorder")
async def reorder_collection_sessions(
    collection_id: str,
    payload: ReorderCollectionSessionsRequest,
) -> dict[str, object]:
    store = get_collection_store()
    try:
        collection = store.reorder_sessions(collection_id, payload.session_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if collection is None:
        raise HTTPException(status_code=404, detail=f"Collection not found: {collection_id}")
    return _detail_from_collection(collection).model_dump()


@router.get("/collections/{collection_id}/bundle")
async def export_collection_bundle(collection_id: str) -> Response:
    store = get_collection_store()
    collection = store.get(collection_id)
    if collection is None:
        raise HTTPException(status_code=404, detail=f"Collection not found: {collection_id}")

    payload = _collection_bundle_payload(collection)
    return Response(
        content=json.dumps(payload, indent=2) + "\n",
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={collection.id}.bundle.json"},
    )
