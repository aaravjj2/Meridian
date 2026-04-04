from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from meridian.workspace.session_store import SaveResearchSessionRequest, get_session_store


router = APIRouter(tags=["workspace"])


@router.get("/research/sessions")
async def list_saved_sessions() -> dict[str, object]:
    store = get_session_store()
    sessions = store.list_sessions()
    return {
        "sessions": [item.model_dump() for item in sessions],
        "count": len(sessions),
    }


@router.post("/research/sessions")
async def save_research_session(payload: SaveResearchSessionRequest) -> dict[str, object]:
    store = get_session_store()
    saved = store.save(payload)
    return saved.model_dump()


@router.get("/research/sessions/{saved_id}")
async def get_saved_session(saved_id: str) -> dict[str, object]:
    store = get_session_store()
    saved = store.get(saved_id)
    if saved is None:
        raise HTTPException(status_code=404, detail=f"Saved session not found: {saved_id}")
    return saved.model_dump()


@router.get("/research/sessions/{saved_id}/export")
async def export_saved_session(
    saved_id: str,
    format: str = Query(default="json", pattern="^(json|markdown)$"),
) -> Response:
    store = get_session_store()
    saved = store.get(saved_id)
    if saved is None:
        raise HTTPException(status_code=404, detail=f"Saved session not found: {saved_id}")

    if format == "markdown":
        content = store.export_markdown(saved)
        filename = f"{saved.id}.md"
        media_type = "text/markdown; charset=utf-8"
    else:
        content = saved.model_dump_json(indent=2) + "\n"
        filename = f"{saved.id}.json"
        media_type = "application/json"

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
