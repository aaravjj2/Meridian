from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Query

from apps.api.deps import fixtures_dir


router = APIRouter(tags=["screener"])


def _snapshot_path() -> Path:
    return fixtures_dir() / "screener_snapshot.json"


@router.get("/screener")
async def get_screener(
    category: str | None = Query(default=None),
    platform: str | None = Query(default=None),
    min_dislocation: float = Query(default=0.0, ge=0.0),
    limit: int = Query(default=20, ge=1, le=200),
) -> dict[str, object]:
    payload = json.loads(_snapshot_path().read_text(encoding="utf-8"))
    contracts = list(payload.get("contracts", []))

    if category:
        contracts = [item for item in contracts if item.get("category") == category]
    if platform:
        contracts = [item for item in contracts if item.get("platform") == platform]

    contracts = [item for item in contracts if float(item.get("dislocation", 0.0)) >= min_dislocation]
    contracts.sort(key=lambda item: float(item.get("dislocation", 0.0)), reverse=True)
    contracts = contracts[:limit]

    return {
        "contracts": contracts,
        "scored_at": payload.get("scored_at"),
        "count": len(contracts),
    }
