from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from apps.api.deps import fixtures_dir


router = APIRouter(tags=["markets"])


def _markets_path() -> Path:
    return fixtures_dir() / "markets" / "markets.json"


def _screener_snapshot_path() -> Path:
    return fixtures_dir() / "screener_snapshot.json"


def _load_markets() -> list[dict]:
    return list(json.loads(_markets_path().read_text(encoding="utf-8")))


@router.get("/markets")
async def get_markets(
    category: str | None = Query(default=None),
    platform: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict[str, object]:
    markets = _load_markets()
    if category:
        markets = [item for item in markets if item.get("category") == category]
    if platform:
        markets = [item for item in markets if item.get("platform") == platform]

    start = (page - 1) * page_size
    end = start + page_size
    paged = markets[start:end]

    return {
        "markets": paged,
        "count": len(markets),
        "page": page,
        "page_size": page_size,
    }


@router.get("/markets/{market_id}")
async def get_market_detail(market_id: str) -> dict[str, object]:
    for market in _load_markets():
        if market.get("id") == market_id:
            return market
    raise HTTPException(status_code=404, detail=f"Market not found: {market_id}")


@router.get("/markets/{market_id}/explain")
async def get_market_explain(market_id: str) -> dict[str, object]:
    snapshot = json.loads(_screener_snapshot_path().read_text(encoding="utf-8"))
    for contract in snapshot.get("contracts", []):
        if contract.get("market_id") == market_id:
            return contract
    raise HTTPException(status_code=404, detail=f"Market score not found: {market_id}")
