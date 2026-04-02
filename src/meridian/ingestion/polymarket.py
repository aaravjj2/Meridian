from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from meridian.settings import FIXTURES_DIR, is_demo_mode


class PricePoint(BaseModel):
    ts: str
    price: float


class RawMarket(BaseModel):
    condition_id: str
    title: str
    category: str
    resolution_date: str
    market_probability: float
    volume_usd: float
    open_interest: float
    last_updated: str
    history: list[PricePoint]


@dataclass(slots=True)
class PolymarketClient:
    demo_mode: bool | None = None
    fixtures_root: Path = FIXTURES_DIR / "polymarket"

    def __post_init__(self) -> None:
        if self.demo_mode is None:
            self.demo_mode = is_demo_mode()

    def get_markets(self, tag: str | None = None) -> list[RawMarket]:
        markets = [RawMarket.model_validate(item) for item in self._load_markets()]
        if tag:
            return [m for m in markets if m.category == tag]
        return markets

    def get_market(self, condition_id: str) -> RawMarket:
        for market in self.get_markets():
            if market.condition_id == condition_id:
                return market
        raise KeyError(f"Polymarket market not found: {condition_id}")

    def get_history(self, condition_id: str) -> list[PricePoint]:
        return self.get_market(condition_id).history

    def _load_markets(self) -> list[dict]:
        fixture = self.fixtures_root / "markets.json"
        if not fixture.exists():
            raise FileNotFoundError(f"Polymarket fixture not found: {fixture}")
        payload = json.loads(fixture.read_text(encoding="utf-8"))
        return list(payload)
