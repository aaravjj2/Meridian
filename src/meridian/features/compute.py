from __future__ import annotations

from typing import Any

import pandas as pd


def yield_curve_slope(series_df: pd.DataFrame) -> dict[str, float]:
    sorted_df = series_df.sort_values("date").reset_index(drop=True)
    current = float(sorted_df.iloc[-1]["value"])
    three_month_lookback = float(sorted_df.iloc[max(0, len(sorted_df) - 4)]["value"])
    return {
        "current_slope": current,
        "delta_3m": current - three_month_lookback,
    }


def recession_signal(series_dict: dict[str, pd.DataFrame]) -> dict[str, float | bool]:
    unrate = series_dict["UNRATE"].sort_values("date").reset_index(drop=True)
    recent = unrate.tail(12)
    current = float(recent.iloc[-1]["value"])
    trough = float(recent["value"].min())
    sahm_gap = current - trough
    return {
        "sahm_gap": sahm_gap,
        "recession_signal": sahm_gap >= 0.5,
    }


def inflation_momentum(cpi_df: pd.DataFrame) -> dict[str, float]:
    sorted_df = cpi_df.sort_values("date").reset_index(drop=True)
    latest = float(sorted_df.iloc[-1]["value"])
    three_months_ago = float(sorted_df.iloc[max(0, len(sorted_df) - 4)]["value"])
    annualized = ((latest / three_months_ago) ** 4 - 1.0) * 100 if three_months_ago else 0.0
    return {
        "inflation_3m_annualized_pct": annualized,
    }


def credit_stress(spread_df: pd.DataFrame) -> dict[str, float]:
    sorted_df = spread_df.sort_values("date").reset_index(drop=True)
    recent = sorted_df.tail(12)
    mean = float(recent["value"].mean())
    std = float(recent["value"].std(ddof=0)) if len(recent) > 1 else 0.0
    current = float(recent.iloc[-1]["value"])
    z_score = 0.0 if std == 0.0 else (current - mean) / std
    return {
        "credit_spread": current,
        "credit_stress_z": z_score,
    }


def monetary_regime(fedfunds_df: pd.DataFrame) -> dict[str, str | float]:
    sorted_df = fedfunds_df.sort_values("date").reset_index(drop=True)
    current = float(sorted_df.iloc[-1]["value"])
    if current >= 4.5:
        label = "restrictive"
    elif current >= 2.0:
        label = "neutral"
    else:
        label = "accommodative"
    return {
        "rate": current,
        "regime": label,
    }


def macro_regime_vector(all_series: dict[str, pd.DataFrame]) -> dict[str, str]:
    slope = yield_curve_slope(all_series["T10Y2Y"])
    inflation = inflation_momentum(all_series["CPIAUCSL"])
    monetary = monetary_regime(all_series["FEDFUNDS"])
    credit = credit_stress(all_series["BAMLH0A0HYM2"])
    labor = recession_signal({"UNRATE": all_series["UNRATE"]})

    growth = "EXPANSION" if slope["current_slope"] > -0.25 else "SLOWDOWN"
    inflation_state = "ELEVATED" if inflation["inflation_3m_annualized_pct"] > 2.5 else "COOLING"
    monetary_state = str(monetary["regime"]).upper()
    credit_state = "CAUTION" if credit["credit_stress_z"] > 0.7 else "NORMAL"
    labor_state = "SOFTENING" if labor["recession_signal"] else "TIGHT"

    return {
        "growth": growth,
        "inflation": inflation_state,
        "monetary": monetary_state,
        "credit": credit_state,
        "labor": labor_state,
    }


def flatten_feature_snapshot(all_series: dict[str, pd.DataFrame]) -> dict[str, Any]:
    slope = yield_curve_slope(all_series["T10Y2Y"])
    recession = recession_signal({"UNRATE": all_series["UNRATE"]})
    inflation = inflation_momentum(all_series["CPIAUCSL"])
    credit = credit_stress(all_series["BAMLH0A0HYM2"])
    monetary = monetary_regime(all_series["FEDFUNDS"])
    regime = macro_regime_vector(all_series)

    return {
        "yield_curve_current": round(float(slope["current_slope"]), 6),
        "yield_curve_delta_3m": round(float(slope["delta_3m"]), 6),
        "sahm_gap": round(float(recession["sahm_gap"]), 6),
        "recession_signal": bool(recession["recession_signal"]),
        "inflation_3m_annualized_pct": round(float(inflation["inflation_3m_annualized_pct"]), 6),
        "credit_spread": round(float(credit["credit_spread"]), 6),
        "credit_stress_z": round(float(credit["credit_stress_z"]), 6),
        "fed_funds": round(float(monetary["rate"]), 6),
        "monetary_regime": str(monetary["regime"]),
        "regime_growth": regime["growth"],
        "regime_inflation": regime["inflation"],
        "regime_monetary": regime["monetary"],
        "regime_credit": regime["credit"],
        "regime_labor": regime["labor"],
    }
