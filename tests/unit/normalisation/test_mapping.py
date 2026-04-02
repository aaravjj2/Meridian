from __future__ import annotations

from meridian.normalisation.mapping import CATEGORY_TO_FRED, ContractMapper
from meridian.normalisation.schemas import CanonicalMarket


def make_market(category: str) -> CanonicalMarket:
    return CanonicalMarket(
        id="m1",
        platform="kalshi",
        title="Sample",
        category=category,
        resolution_date="2026-12-31",
        market_probability=0.5,
        volume_usd=1000,
        open_interest=100,
        last_updated="2026-03-31T00:00:00Z",
        history=[],
    )


def test_every_category_maps_to_two_or_more_series() -> None:
    for category, series in CATEGORY_TO_FRED.items():
        assert len(series) >= 2, f"{category} has insufficient mappings"


def test_contract_mapper_returns_category_series() -> None:
    mapper = ContractMapper()
    market = make_market("recession")
    series = mapper.get_relevant_series(market)
    assert len(series) >= 2
    assert "T10Y2Y" in series
