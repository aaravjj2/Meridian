from __future__ import annotations

import json
from pathlib import Path

from meridian.ingestion.fred import FredClient
from meridian.models.fair_value import FairValueModel
from meridian.normalisation.schemas import CanonicalMarket


ROOT = Path(__file__).resolve().parents[3]


def _market() -> CanonicalMarket:
    markets = json.loads((ROOT / "data" / "fixtures" / "markets" / "markets.json").read_text(encoding="utf-8"))
    return CanonicalMarket.model_validate(markets[0])


def _macro_series() -> dict:
    fred = FredClient(demo_mode=True)
    return {
        "FEDFUNDS": fred.fetch_series("FEDFUNDS"),
        "T10Y2Y": fred.fetch_series("T10Y2Y"),
        "CPIAUCSL": fred.fetch_series("CPIAUCSL"),
        "UNRATE": fred.fetch_series("UNRATE"),
        "GDPC1": fred.fetch_series("GDPC1"),
        "BAMLH0A0HYM2": fred.fetch_series("BAMLH0A0HYM2"),
        "M2SL": fred.fetch_series("M2SL"),
    }


def test_fair_value_score_range() -> None:
    model = FairValueModel()
    score = model.score(_market(), _macro_series())
    assert 0.0 <= score <= 1.0


def test_fair_value_uncertainty_band() -> None:
    model = FairValueModel()
    score, lower, upper = model.predict_with_interval(_market(), _macro_series())
    assert lower <= score <= upper
    assert 0.0 <= lower <= 1.0
    assert 0.0 <= upper <= 1.0
