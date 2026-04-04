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
