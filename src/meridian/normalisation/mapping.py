from __future__ import annotations

from dataclasses import dataclass

from meridian.normalisation.schemas import CanonicalMarket


CATEGORY_TO_FRED: dict[str, list[str]] = {
    "fed_policy": ["FEDFUNDS", "T10Y2Y"],
    "inflation": ["CPIAUCSL", "PCEPI"],
    "employment": ["UNRATE", "ICSA"],
    "recession": ["T10Y2Y", "GDPC1", "USREC"],
    "gdp": ["GDPC1", "M2SL"],
    "geopolitical": ["BAMLH0A0HYM2", "DCOILWTICO"],
    "other": ["FEDFUNDS", "UNRATE"],
}


@dataclass(slots=True)
class ContractMapper:
    mapping: dict[str, list[str]] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.mapping is None:
            self.mapping = CATEGORY_TO_FRED

    def get_relevant_series(self, market: CanonicalMarket) -> list[str]:
        return list(self.mapping.get(market.category, self.mapping["other"]))
