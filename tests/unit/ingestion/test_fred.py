from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from meridian.ingestion.fred import FredClient


@pytest.fixture
def fred_client() -> FredClient:
    return FredClient(demo_mode=True)


def test_fetch_series_returns_dataframe_shape(fred_client: FredClient) -> None:
    df = fred_client.fetch_series("T10Y2Y")
    assert list(df.columns) == ["date", "value"]
    assert len(df) >= 5
    assert df["value"].dtype.kind in {"f", "i"}


def test_demo_mode_bypasses_live_fetch(monkeypatch: pytest.MonkeyPatch, fred_client: FredClient) -> None:
    called = {"live": False}

    def _boom(self, *args, **kwargs):
        called["live"] = True
        raise RuntimeError("live fetch should not be called in demo mode")

    monkeypatch.setattr(FredClient, "_fetch_live", _boom)
    fred_client.fetch_series("UNRATE")
    assert called["live"] is False


def test_cache_hit_skips_live_fetch(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = FredClient(demo_mode=False, cache_root=tmp_path / "cache", api_key="test")
    data_path = client.cache_root / "CPIAUCSL.json"
    meta_path = client.cache_root / "CPIAUCSL.meta.json"

    payload = {
        "series_id": "CPIAUCSL",
        "name": "CPI",
        "frequency": "Monthly",
        "observations": [
            {"date": "2026-01-01", "value": "317.9"},
            {"date": "2026-02-01", "value": "318.2"},
        ],
    }
    data_path.write_text(json.dumps(payload), encoding="utf-8")
    meta_path.write_text(
        json.dumps({"expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat()}),
        encoding="utf-8",
    )

    def _boom(self, *args, **kwargs):
        raise RuntimeError("expected cache hit")

    monkeypatch.setattr(FredClient, "_fetch_live", _boom)
    df = client.fetch_series("CPIAUCSL")
    assert len(df) == 2


def test_search_returns_matched_series(fred_client: FredClient) -> None:
    results = fred_client.search("mortgage")
    assert len(results) >= 1
    assert any(item.series_id == "MORTGAGE30US" for item in results)
