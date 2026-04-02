from __future__ import annotations

from datetime import UTC, datetime

from meridian.normalisation.schemas import CanonicalMarket, MispricingScore


def _iso_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def score_dislocation(
    market: CanonicalMarket,
    model_prob: float,
    lower: float | None = None,
    upper: float | None = None,
    scored_at: str | None = None,
) -> MispricingScore:
    market_prob = float(market.market_probability)
    model_prob = float(model_prob)

    dislocation = abs(market_prob - model_prob)
    direction = "market_overpriced" if market_prob > model_prob else "market_underpriced"

    interval_width = (upper - lower) if (lower is not None and upper is not None) else 0.20
    base_conf = int(round(dislocation * 10))
    if interval_width < 0.18:
        base_conf += 1
    if interval_width > 0.32:
        base_conf -= 1
    confidence = max(1, min(5, base_conf))

    gap_pp = (model_prob - market_prob) * 100
    if direction == "market_underpriced":
        summary = "underpricing"
    else:
        summary = "overpricing"

    explanation = (
        f"Model probability differs by {abs(gap_pp):.1f}pp from market-implied odds, "
        f"indicating potential {summary}."
    )

    return MispricingScore(
        market_id=market.id,
        market_prob=market_prob,
        model_prob=model_prob,
        dislocation=dislocation,
        direction=direction,
        explanation=explanation,
        confidence=confidence,
        scored_at=scored_at or _iso_now(),
    )
