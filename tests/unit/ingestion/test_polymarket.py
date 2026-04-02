from __future__ import annotations

from meridian.ingestion.polymarket import PolymarketClient


def test_polymarket_get_markets_demo_mode() -> None:
    client = PolymarketClient(demo_mode=True)
    markets = client.get_markets()
    assert len(markets) >= 5
    assert all(m.condition_id for m in markets)


def test_polymarket_get_market_and_history() -> None:
    client = PolymarketClient(demo_mode=True)
    market = client.get_market("pm-fed-cut-june-2026")
    history = client.get_history("pm-fed-cut-june-2026")
    assert market.category == "fed_policy"
    assert len(history) >= 3
    assert all(point.price >= 0 for point in history)


def test_polymarket_tag_filter() -> None:
    client = PolymarketClient(demo_mode=True)
    filtered = client.get_markets(tag="recession")
    assert len(filtered) >= 1
    assert all(item.category == "recession" for item in filtered)
