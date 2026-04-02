from __future__ import annotations

import json
from pathlib import Path

from meridian.normalisation.normalise import assign_category, normalise_kalshi, normalise_polymarket


ROOT = Path(__file__).resolve().parents[3]


def test_assign_category_from_title_keywords() -> None:
    assert assign_category("Will CPI cool this quarter?") == "inflation"
    assert assign_category("Will unemployment rise above 5%?") == "employment"
    assert assign_category("Will real GDP decline?") == "gdp"


def test_normalise_kalshi_round_trip_fields() -> None:
    path = ROOT / "data" / "fixtures" / "kalshi" / "markets.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    market = normalise_kalshi(payload[0])
    assert market.platform == "kalshi"
    assert market.id.startswith("KX")
    assert market.market_probability >= 0
    assert len(market.history) >= 1


def test_normalise_polymarket_round_trip_fields() -> None:
    path = ROOT / "data" / "fixtures" / "polymarket" / "markets.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    market = normalise_polymarket(payload[0])
    assert market.platform == "polymarket"
    assert market.id.startswith("pm-")
    assert market.market_probability >= 0
    assert len(market.history) >= 1
