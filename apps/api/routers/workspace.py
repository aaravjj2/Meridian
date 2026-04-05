from __future__ import annotations

import json
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from meridian.workspace.session_store import SaveResearchSessionRequest, get_session_store


router = APIRouter(tags=["workspace"])


QueryClass = Literal["macro_outlook", "event_probability", "ticker_macro"]


class SessionRenameRequest(BaseModel):
    label: str | None = Field(default=None, max_length=120)


class SessionArchiveRequest(BaseModel):
    archived: bool = True


@router.get("/research/sessions")
async def list_saved_sessions(
    search: str | None = Query(default=None, max_length=120),
    include_archived: bool = Query(default=False),
    query_class: QueryClass | None = Query(default=None),
) -> dict[str, object]:
    store = get_session_store()
    sessions = store.list_sessions(
        search=search,
        include_archived=include_archived,
        query_class=query_class,
    )
    return {
        "sessions": [item.model_dump() for item in sessions],
        "count": len(sessions),
    }


@router.get("/research/sessions/integrity")
async def verify_saved_sessions_integrity(
    search: str | None = Query(default=None, max_length=120),
    include_archived: bool = Query(default=True),
) -> dict[str, object]:
    store = get_session_store()
    reports = store.verify_integrity_all(search=search, include_archived=include_archived)
    healthy_count = sum(1 for report in reports if report.signature_valid and len(report.issues) == 0)
    return {
        "reports": [item.model_dump() for item in reports],
        "count": len(reports),
        "healthy_count": healthy_count,
        "issue_count": len(reports) - healthy_count,
    }


@router.get("/research/sessions/evaluation/dashboard")
async def get_workspace_evaluation_dashboard(
    search: str | None = Query(default=None, max_length=120),
    include_archived: bool = Query(default=False),
    query_class: QueryClass | None = Query(default=None),
) -> dict[str, object]:
    store = get_session_store()
    dashboard = store.build_evaluation_dashboard(
        search=search,
        include_archived=include_archived,
        query_class=query_class,
    )
    return dashboard.model_dump()


@router.get("/research/sessions/evaluation/dashboard/export")
async def export_workspace_evaluation_dashboard(
    search: str | None = Query(default=None, max_length=120),
    include_archived: bool = Query(default=False),
    query_class: QueryClass | None = Query(default=None),
) -> Response:
    store = get_session_store()
    dashboard = store.build_evaluation_dashboard(
        search=search,
        include_archived=include_archived,
        query_class=query_class,
    )
    if not dashboard.ready_for_export:
        raise HTTPException(
            status_code=409,
            detail="Evaluation dashboard is not clean enough for export",
        )

    timestamp = dashboard.generated_at.replace(":", "").replace("-", "")
    filename = f"workspace-evaluation-dashboard-{timestamp}.json"
    return Response(
        content=dashboard.model_dump_json(indent=2) + "\n",
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/research/sessions/compare")
async def compare_saved_sessions(
    left_id: str = Query(min_length=4),
    right_id: str = Query(min_length=4),
) -> dict[str, object]:
    store = get_session_store()
    comparison = store.compare(left_id=left_id, right_id=right_id)
    if comparison is None:
        raise HTTPException(status_code=404, detail="One or both sessions were not found")
    return comparison.model_dump()


@router.post("/research/sessions/{saved_id}/recapture")
async def recapture_saved_session(saved_id: str) -> dict[str, object]:
    store = get_session_store()
    recaptured = store.recapture(saved_id=saved_id)
    if recaptured is None:
        raise HTTPException(status_code=404, detail=f"Saved session not found: {saved_id}")
    return recaptured.model_dump()


@router.post("/research/sessions")
async def save_research_session(payload: SaveResearchSessionRequest) -> dict[str, object]:
    store = get_session_store()
    saved = store.save(payload)
    return saved.model_dump()


@router.patch("/research/sessions/{saved_id}/rename")
async def rename_saved_session(saved_id: str, payload: SessionRenameRequest) -> dict[str, object]:
    store = get_session_store()
    saved = store.rename(saved_id=saved_id, label=payload.label)
    if saved is None:
        raise HTTPException(status_code=404, detail=f"Saved session not found: {saved_id}")
    return saved.model_dump()


@router.patch("/research/sessions/{saved_id}/archive")
async def archive_saved_session(saved_id: str, payload: SessionArchiveRequest) -> dict[str, object]:
    store = get_session_store()
    saved = store.set_archived(saved_id=saved_id, archived=payload.archived)
    if saved is None:
        raise HTTPException(status_code=404, detail=f"Saved session not found: {saved_id}")
    return saved.model_dump()


@router.delete("/research/sessions/{saved_id}")
async def delete_saved_session(saved_id: str) -> dict[str, object]:
    store = get_session_store()
    deleted = store.delete(saved_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Saved session not found: {saved_id}")
    return {"deleted": True, "id": saved_id}


@router.get("/research/sessions/{saved_id}")
async def get_saved_session(saved_id: str) -> dict[str, object]:
    store = get_session_store()
    saved = store.get(saved_id)
    if saved is None:
        raise HTTPException(status_code=404, detail=f"Saved session not found: {saved_id}")
    return saved.model_dump()


@router.get("/research/sessions/{saved_id}/timeline")
async def get_saved_session_timeline(
    saved_id: str,
    include_archived: bool = Query(default=True),
) -> dict[str, object]:
    store = get_session_store()
    saved = store.get(saved_id)
    if saved is None:
        raise HTTPException(status_code=404, detail=f"Saved session not found: {saved_id}")

    timeline = store.build_thread_timeline(
        session_id=saved.session_id,
        include_archived=include_archived,
    )
    return timeline.model_dump()


@router.get("/research/sessions/{saved_id}/integrity")
async def verify_saved_session_integrity(saved_id: str) -> dict[str, object]:
    store = get_session_store()
    report = store.verify_integrity(saved_id=saved_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Saved session not found: {saved_id}")
    return report.model_dump()


@router.get("/research/sessions/{saved_id}/review")
async def review_saved_session(saved_id: str) -> dict[str, object]:
    store = get_session_store()
    checklist = store.review(saved_id=saved_id)
    if checklist is None:
        raise HTTPException(status_code=404, detail=f"Saved session not found: {saved_id}")
    return checklist.model_dump()


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


@router.get("/research/sessions/{saved_id}/bundle")
async def export_saved_bundle(saved_id: str) -> Response:
    store = get_session_store()
    saved = store.get(saved_id)
    if saved is None:
        raise HTTPException(status_code=404, detail=f"Saved session not found: {saved_id}")

    payload = store.export_bundle_payload(saved)
    return Response(
        content=json.dumps(payload, indent=2) + "\n",
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={saved.id}.bundle.json"},
    )
