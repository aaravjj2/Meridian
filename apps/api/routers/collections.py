from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from meridian.workspace.collection_store import get_collection_store


router = APIRouter(tags=["collections"])


class CollectionListResponse(BaseModel):
    collections: list[dict[str, Any]]
    count: int


@router.post("/collections")
async def create_collection(payload: dict[str, Any]) -> dict[str, Any]:
    from meridian.normalisation.schemas import CreateCollectionRequest

    store = get_collection_store()
    request = CreateCollectionRequest(**payload)
    collection = store.create(request)
    return collection.model_dump()


@router.get("/collections")
async def list_collections() -> dict[str, Any]:
    store = get_collection_store()
    summaries = store.list_collections()
    return {
        "collections": [item.model_dump() for item in summaries],
        "count": len(summaries),
    }


@router.get("/collections/{collection_id}")
async def get_collection(collection_id: str) -> dict[str, Any]:
    store = get_collection_store()
    collection = store.get(collection_id)
    if collection is None:
        raise HTTPException(status_code=404, detail=f"Collection not found: {collection_id}")
    return collection.model_dump()


@router.patch("/collections/{collection_id}")
async def update_collection(collection_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    from meridian.normalisation.schemas import UpdateCollectionRequest

    store = get_collection_store()
    request = UpdateCollectionRequest(**payload)
    collection = store.update(collection_id, request)
    if collection is None:
        raise HTTPException(status_code=404, detail=f"Collection not found: {collection_id}")
    return collection.model_dump()


@router.delete("/collections/{collection_id}")
async def delete_collection(collection_id: str) -> dict[str, Any]:
    store = get_collection_store()
    deleted = store.delete(collection_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Collection not found: {collection_id}")
    return {"deleted": True, "id": collection_id}


@router.post("/collections/{collection_id}/sessions")
async def add_session_to_collection(collection_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    from meridian.normalisation.schemas import AddSessionToCollectionRequest

    store = get_collection_store()
    request = AddSessionToCollectionRequest(**payload)
    collection = store.add_session(collection_id, request)
    if collection is None:
        raise HTTPException(status_code=404, detail=f"Collection not found: {collection_id}")
    return collection.model_dump()


@router.delete("/collections/{collection_id}/sessions/{session_id}")
async def remove_session_from_collection(collection_id: str, session_id: str) -> dict[str, Any]:
    store = get_collection_store()
    collection = store.remove_session(collection_id, session_id)
    if collection is None:
        raise HTTPException(status_code=404, detail=f"Collection not found: {collection_id}")
    return collection.model_dump()


@router.put("/collections/{collection_id}/sessions/reorder")
async def reorder_collection_sessions(collection_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    from meridian.normalisation.schemas import ReorderCollectionSessionsRequest

    store = get_collection_store()
    request = ReorderCollectionSessionsRequest(**payload)
    try:
        collection = store.reorder_sessions(collection_id, request.session_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if collection is None:
        raise HTTPException(status_code=404, detail=f"Collection not found: {collection_id}")
    return collection.model_dump()
