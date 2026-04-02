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


def cross_series_correlation(
    series_dict: dict[str, pd.DataFrame],
    lookback_periods: int = 52,
) -> dict[str, Any]:
    """
    Compute rolling correlations between multiple economic series.
    Useful for identifying leading indicators and regime changes.
    """
    merged = None
    for name, df in series_dict.items():
        sorted_df = df.sort_values("date").reset_index(drop=True)
        sorted_df = sorted_df.tail(lookback_periods).copy()
        sorted_df = sorted_df.rename(columns={"value": name})
        if merged is None:
            merged = sorted_df[["date", name]]
        else:
            merged = merged.merge(sorted_df[["date", name]], on="date", how="inner")

    if merged is None or len(merged) < 3:
        return {"error": "Insufficient data for correlation analysis"}

    numeric_cols = [c for c in merged.columns if c != "date"]
    corr_matrix = merged[numeric_cols].corr()

    correlations = []
    for i, col1 in enumerate(numeric_cols):
        for j, col2 in enumerate(numeric_cols):
            if i < j:
                corr_val = float(corr_matrix.loc[col1, col2])
                correlations.append({
                    "series_1": col1,
                    "series_2": col2,
                    "correlation": round(corr_val, 4),
                    "strength": "strong" if abs(corr_val) > 0.7 else "moderate" if abs(corr_val) > 0.4 else "weak",
                })

    return {
        "lookback_periods": lookback_periods,
        "observations": len(merged),
        "correlations": correlations,
    }


def composite_indicator(
    series_dict: dict[str, pd.DataFrame],
    weights: dict[str, float] | None = None,
    lookback_periods: int = 12,
) -> dict[str, Any]:
    """
    Build a composite indicator from multiple economic series.
    Normalizes each series to z-scores and combines with weights.
    """
    if weights is None:
        weights = {name: 1.0 for name in series_dict.keys()}

    # Normalize and combine
    merged = None
    for name, df in series_dict.items():
        sorted_df = df.sort_values("date").reset_index(drop=True)
        sorted_df = sorted_df.tail(lookback_periods * 2).copy()  # Extra for historical context

        # Compute z-scores
        mean = float(sorted_df["value"].mean())
        std = float(sorted_df["value"].std())
        if std == 0:
            std = 1

        sorted_df[f"{name}_z"] = (sorted_df["value"] - mean) / std

        if merged is None:
            merged = sorted_df[["date", f"{name}_z"]]
        else:
            merged = merged.merge(sorted_df[["date", f"{name}_z"]], on="date", how="outer")

    if merged is None:
        return {"error": "No data available"}

    # Compute weighted composite
    z_cols = [c for c in merged.columns if c.endswith("_z")]
    merged = merged.dropna()

    merged["composite"] = sum(merged[col] * weights.get(col.replace("_z", ""), 1.0) for col in z_cols) / len(z_cols)

    latest = float(merged.iloc[-1]["composite"])
    mean_val = float(merged["composite"].mean())
    std_val = float(merged["composite"].std())

    percentile = ((latest - mean_val) / std_val + 3) / 6 * 100  # Rough percentile
    percentile = max(0, min(100, percentile))

    return {
        "composite_value": round(latest, 4),
        "composite_mean": round(mean_val, 4),
        "composite_std": round(std_val, 4),
        "percentile": round(percentile, 1),
        "interpretation": "elevated" if percentile > 75 else "depressed" if percentile < 25 else "normal",
        "observations": len(merged),
    }


def regime_transition_probability(
    series_dict: dict[str, pd.DataFrame],
    lookback_weeks: int = 104,
) -> dict[str, Any]:
    """
    Estimate probability of regime transition using multiple indicators.
    Uses a weighted signal approach similar to Sahm rule methodology.
    """
    # Get current regime state
    regime = macro_regime_vector(series_dict)

    # Count stress signals
    stress_signals = 0
    total_signals = 0

    # Growth signal
    if regime["growth"] == "SLOWDOWN":
        stress_signals += 1
    total_signals += 1

    # Inflation signal
    if regime["inflation"] == "ELEVATED":
        stress_signals += 1
    total_signals += 1

    # Credit stress
    if regime["credit"] == "CAUTION":
        stress_signals += 1
    total_signals += 1

    # Labor softening
    if regime["labor"] == "SOFTENING":
        stress_signals += 1
    total_signals += 1

    # Monetary regime - restrictive policy increases transition risk
    if regime["monetary"] == "RESTRICTIVE":
        stress_signals += 0.5
    total_signals += 1

    # Calculate transition probability
    transition_prob = stress_signals / total_signals

    return {
        "regime_transition_probability": round(transition_prob, 4),
        "transition_probability_pct": round(transition_prob * 100, 1),
        "current_regime": regime,
        "stress_signals": stress_signals,
        "total_signals": total_signals,
        "interpretation": (
            "high" if transition_prob > 0.6 else "moderate" if transition_prob > 0.3 else "low"
        ),
    }
