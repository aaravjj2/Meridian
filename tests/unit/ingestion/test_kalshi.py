from __future__ import annotations

from meridian.ingestion.kalshi import KalshiClient


def test_kalshi_get_markets_demo_mode() -> None:
    client = KalshiClient(demo_mode=True)
    markets = client.get_markets()
    assert len(markets) >= 5
    assert all(m.ticker for m in markets)


def test_kalshi_get_market_and_history() -> None:
    client = KalshiClient(demo_mode=True)
    market = client.get_market("KXFEDCUT-H1-2026")
    history = client.get_history("KXFEDCUT-H1-2026")
    assert market.category == "fed_policy"
    assert len(history) >= 3
    assert all(point.price >= 0 for point in history)


def test_kalshi_category_filter() -> None:
    client = KalshiClient(demo_mode=True)
    filtered = client.get_markets(category="inflation")
    assert len(filtered) >= 1
    assert all(item.category == "inflation" for item in filtered)
