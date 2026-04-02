from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from meridian.normalisation.mapping import ContractMapper
from meridian.normalisation.schemas import CanonicalMarket


def _series_signal(series: pd.DataFrame) -> float:
    sorted_df = series.sort_values("date").reset_index(drop=True)
    latest = float(sorted_df.iloc[-1]["value"])
    mean = float(sorted_df["value"].mean())
    std = float(sorted_df["value"].std(ddof=0)) if len(sorted_df) > 1 else 0.0
    if std == 0.0:
        return 0.0
    return (latest - mean) / std


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


@dataclass(slots=True)
class FairValueModel:
    mapper: ContractMapper | None = None
    platt_a: float = 3.0
    platt_b: float = 0.0

    def __post_init__(self) -> None:
        if self.mapper is None:
            self.mapper = ContractMapper()

    def score(self, market: CanonicalMarket, macro_series: dict[str, pd.DataFrame]) -> float:
        score, _, _ = self.predict_with_interval(market, macro_series)
        return score

    def predict_with_interval(self, market: CanonicalMarket, macro_series: dict[str, pd.DataFrame]) -> tuple[float, float, float]:
        assert self.mapper is not None
        relevant = self.mapper.get_relevant_series(market)

        signals: list[float] = []
        for series_id in relevant:
            frame = macro_series.get(series_id)
            if frame is None or frame.empty:
                continue
            signals.append(_series_signal(frame))

        if signals:
            average_signal = sum(signals) / len(signals)
            dispersion = sum(abs(s - average_signal) for s in signals) / len(signals)
        else:
            average_signal = 0.0
            dispersion = 1.0

        raw_score = 0.5 + 0.12 * average_signal
        calibrated = _sigmoid(self.platt_a * (raw_score - 0.5) + self.platt_b)
        calibrated = min(0.99, max(0.01, calibrated))

        uncertainty = min(0.25, 0.08 + 0.05 * dispersion)
        lower = max(0.0, calibrated - uncertainty)
        upper = min(1.0, calibrated + uncertainty)

        return calibrated, lower, upper
