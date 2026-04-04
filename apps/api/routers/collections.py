from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from meridian.normalisation.schemas import (
    AddSessionToCollectionRequest,
    CreateCollectionRequest,
    ReorderCollectionSessionsRequest,
    ResearchCollection,
    ResearchCollectionDetail,
    ResearchCollectionSummary,
    ResearchCollectionTimelineEntry,
    UpdateCollectionRequest,
)
from meridian.workspace.collection_store import get_collection_store
from meridian.workspace.session_store import get_session_store


router = APIRouter(tags=["collections"])


class CollectionListResponse(BaseModel):
    collections: list[ResearchCollectionSummary]
    count: int


def _detail_from_collection(collection: ResearchCollection) -> ResearchCollectionDetail:
    session_store = get_session_store()
    summaries = session_store.list_sessions(include_archived=True)
    summary_index = {item.id: item for item in summaries}

    timeline: list[ResearchCollectionTimelineEntry] = []
    missing_session_count = 0
    for session_id in collection.session_ids:
        summary = summary_index.get(session_id)
        if summary is None:
            timeline.append(
                ResearchCollectionTimelineEntry(
                    session_id=session_id,
                    exists=False,
                )
            )
            missing_session_count += 1
            continue

        timeline.append(
            ResearchCollectionTimelineEntry(
                session_id=summary.id,
                exists=True,
                label=summary.label,
                question=summary.question,
                query_class=summary.query_class,
                saved_at=summary.saved_at,
                evaluation_passed=summary.evaluation_passed,
                snapshot_signature=summary.snapshot_signature,
                archived=summary.archived,
            )
        )

    return ResearchCollectionDetail(
        collection=collection,
        timeline=timeline,
        missing_session_count=missing_session_count,
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
