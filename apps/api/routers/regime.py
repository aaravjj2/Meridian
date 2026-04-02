from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter

from apps.api.deps import fixtures_dir


router = APIRouter(tags=["regime"])


def _snapshot_path() -> Path:
    return fixtures_dir() / "regime_snapshot.json"


@router.get("/regime")
async def get_regime() -> dict[str, object]:
    return json.loads(_snapshot_path().read_text(encoding="utf-8"))
