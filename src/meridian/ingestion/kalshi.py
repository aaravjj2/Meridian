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
    ticker: str
    title: str
    category: str
    resolution_date: str
    market_probability: float
    volume_usd: float
    open_interest: float
    last_updated: str
    history: list[PricePoint]


@dataclass(slots=True)
class KalshiClient:
    demo_mode: bool | None = None
    fixtures_root: Path = FIXTURES_DIR / "kalshi"

    def __post_init__(self) -> None:
        if self.demo_mode is None:
            self.demo_mode = is_demo_mode()

    def get_markets(self, category: str | None = None) -> list[RawMarket]:
        markets = [RawMarket.model_validate(item) for item in self._load_markets()]
        if category:
            return [m for m in markets if m.category == category]
        return markets

    def get_market(self, ticker: str) -> RawMarket:
        for market in self.get_markets():
            if market.ticker == ticker:
                return market
        raise KeyError(f"Kalshi market not found: {ticker}")

    def get_history(self, ticker: str) -> list[PricePoint]:
        return self.get_market(ticker).history

    def _load_markets(self) -> list[dict]:
        fixture = self.fixtures_root / "markets.json"
        if not fixture.exists():
            raise FileNotFoundError(f"Kalshi fixture not found: {fixture}")
        payload = json.loads(fixture.read_text(encoding="utf-8"))
        return list(payload)
