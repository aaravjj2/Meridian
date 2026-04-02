from __future__ import annotations

from typing import Any

from meridian.normalisation.schemas import CanonicalMarket, DataPoint


CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "fed_policy": ("fed", "rate", "fomc", "cut", "hike"),
    "inflation": ("inflation", "cpi", "pce", "prices"),
    "employment": ("unemployment", "jobs", "labor", "payroll"),
    "recession": ("recession", "nber", "contraction"),
    "gdp": ("gdp", "growth"),
    "geopolitical": ("war", "tariff", "sanction", "geopolitical"),
}


MANUAL_CATEGORY_OVERRIDES: dict[str, str] = {}


def assign_category(title: str, market_id: str | None = None) -> str:
    if market_id and market_id in MANUAL_CATEGORY_OVERRIDES:
        return MANUAL_CATEGORY_OVERRIDES[market_id]

    lowered = title.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return "other"


def _coerce_history(history: list[dict[str, Any]]) -> list[DataPoint]:
    output: list[DataPoint] = []
    for row in history:
        ts = row.get("ts") or row.get("date")
        output.append(DataPoint(date=str(ts), value=float(row["price"] if "price" in row else row["value"])))
    return output


def normalise_kalshi(raw: dict[str, Any]) -> CanonicalMarket:
    market_id = str(raw["ticker"])
    title = str(raw["title"])
    category = str(raw.get("category") or assign_category(title, market_id=market_id))

    return CanonicalMarket(
        id=market_id,
        platform="kalshi",
        title=title,
        category=category,
        resolution_date=str(raw["resolution_date"]),
        market_probability=float(raw["market_probability"]),
        volume_usd=float(raw.get("volume_usd", 0.0)),
        open_interest=float(raw.get("open_interest", 0.0)),
        last_updated=str(raw["last_updated"]),
        history=_coerce_history(list(raw.get("history", []))),
    )


def normalise_polymarket(raw: dict[str, Any]) -> CanonicalMarket:
    market_id = str(raw["condition_id"])
    title = str(raw["title"])
    category = str(raw.get("category") or assign_category(title, market_id=market_id))

    return CanonicalMarket(
        id=market_id,
        platform="polymarket",
        title=title,
        category=category,
        resolution_date=str(raw["resolution_date"]),
        market_probability=float(raw["market_probability"]),
        volume_usd=float(raw.get("volume_usd", 0.0)),
        open_interest=float(raw.get("open_interest", 0.0)),
        last_updated=str(raw["last_updated"]),
        history=_coerce_history(list(raw.get("history", []))),
    )
