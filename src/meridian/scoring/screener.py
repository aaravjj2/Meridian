from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd

from meridian.ingestion.fred import FredClient
from meridian.models.fair_value import FairValueModel
from meridian.normalisation.schemas import CanonicalMarket, MispricingScore
from meridian.scoring.score import score_dislocation


SERIES_FOR_SCORING = [
    "FEDFUNDS",
    "T10Y2Y",
    "CPIAUCSL",
    "UNRATE",
    "GDPC1",
    "BAMLH0A0HYM2",
    "M2SL",
    "MORTGAGE30US",
]


def load_macro_series_for_scoring(demo_mode: bool = True) -> dict[str, pd.DataFrame]:
    fred = FredClient(demo_mode=demo_mode)
    series: dict[str, pd.DataFrame] = {}
    for series_id in SERIES_FOR_SCORING:
        try:
            series[series_id] = fred.fetch_series(series_id)
        except FileNotFoundError:
            # Optional mapping series can be absent in demo fixtures.
            continue
    return series


def _parse_iso_date(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def run_screener(
    markets: list[CanonicalMarket],
    macro_series: dict[str, pd.DataFrame],
    model: FairValueModel | None = None,
    now: datetime | None = None,
) -> list[MispricingScore]:
    model = model or FairValueModel()
    now = now or datetime.now(UTC)
    horizon = now + timedelta(days=90)

    scored: list[MispricingScore] = []
    for market in markets:
        resolution = _parse_iso_date(market.resolution_date)
        if resolution > horizon:
            continue

        probability, lower, upper = model.predict_with_interval(market, macro_series)
        scored.append(
            score_dislocation(
                market=market,
                model_prob=probability,
                lower=lower,
                upper=upper,
                scored_at=now.isoformat().replace("+00:00", "Z"),
            )
        )

    scored.sort(key=lambda item: item.dislocation, reverse=True)
    return scored
