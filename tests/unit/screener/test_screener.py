from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from meridian.normalisation.schemas import CanonicalMarket
from meridian.scoring.screener import load_macro_series_for_scoring, run_screener


ROOT = Path(__file__).resolve().parents[3]


def _markets() -> list[CanonicalMarket]:
    payload = json.loads((ROOT / "data" / "fixtures" / "markets" / "markets.json").read_text(encoding="utf-8"))
    return [CanonicalMarket.model_validate(item) for item in payload]


def test_run_screener_sorted_by_dislocation() -> None:
    scores = run_screener(
        _markets(),
        load_macro_series_for_scoring(demo_mode=True),
        now=datetime(2026, 4, 2, tzinfo=UTC),
    )
    assert len(scores) >= 1
    assert all(0.0 <= item.dislocation <= 1.0 for item in scores)
    assert scores == sorted(scores, key=lambda item: item.dislocation, reverse=True)


def test_run_screener_outputs_valid_direction_and_confidence() -> None:
    scores = run_screener(
        _markets(),
        load_macro_series_for_scoring(demo_mode=True),
        now=datetime(2026, 4, 2, tzinfo=UTC),
    )
    assert all(item.direction in {"market_overpriced", "market_underpriced"} for item in scores)
    assert all(1 <= item.confidence <= 5 for item in scores)
