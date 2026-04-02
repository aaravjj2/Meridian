from __future__ import annotations

from meridian.features.compute import (
    credit_stress,
    flatten_feature_snapshot,
    inflation_momentum,
    macro_regime_vector,
    monetary_regime,
    recession_signal,
    yield_curve_slope,
)
from meridian.ingestion.fred import FredClient


def _series() -> dict:
    client = FredClient(demo_mode=True)
    return {
        "T10Y2Y": client.fetch_series("T10Y2Y"),
        "UNRATE": client.fetch_series("UNRATE"),
        "CPIAUCSL": client.fetch_series("CPIAUCSL"),
        "FEDFUNDS": client.fetch_series("FEDFUNDS"),
        "BAMLH0A0HYM2": client.fetch_series("BAMLH0A0HYM2"),
    }


def test_feature_functions_return_expected_keys() -> None:
    series = _series()

    assert set(yield_curve_slope(series["T10Y2Y"])) == {"current_slope", "delta_3m"}
    assert set(recession_signal({"UNRATE": series["UNRATE"]})) == {"sahm_gap", "recession_signal"}
    assert set(inflation_momentum(series["CPIAUCSL"])) == {"inflation_3m_annualized_pct"}
    assert set(credit_stress(series["BAMLH0A0HYM2"])) == {"credit_spread", "credit_stress_z"}
    assert set(monetary_regime(series["FEDFUNDS"])) == {"rate", "regime"}


def test_macro_regime_vector_and_flattened_snapshot() -> None:
    series = _series()
    regime = macro_regime_vector(series)
    snapshot = flatten_feature_snapshot(series)

    assert set(regime.keys()) == {"growth", "inflation", "monetary", "credit", "labor"}
    assert "yield_curve_current" in snapshot
    assert "regime_growth" in snapshot
