from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel, Field

from meridian.features.compute import (
    composite_indicator,
    credit_stress,
    inflation_momentum,
    monetary_regime,
    regime_transition_probability,
    yield_curve_slope,
)

# Import cross_series_correlation with a compatible name
from meridian.features.compute import cross_series_correlation as correlation_analysis
from meridian.ingestion.edgar import EdgarClient
from meridian.ingestion.fred import FredClient
from meridian.ingestion.kalshi import KalshiClient
from meridian.ingestion.news import NewsClient
from meridian.ingestion.polymarket import PolymarketClient
from meridian.vector.store import VectorStore, seed_default_documents


class FredFetchInput(BaseModel):
    series_id: str
    start_date: str | None = None
    end_date: str | None = None


class FredSearchInput(BaseModel):
    query: str
    limit: int = Field(default=10, ge=1, le=50)


class PredictionMarketFetchInput(BaseModel):
    platform: str = Field(description="kalshi or polymarket")
    event_slug: str


class EdgarFetchInput(BaseModel):
    ticker: str
    form_type: str = "10-K"


class NewsFetchInput(BaseModel):
    topic: str
    days_back: int = Field(default=7, ge=1, le=30)


class VectorSearchInput(BaseModel):
    query: str
    top_k: int = Field(default=3, ge=1, le=10)


class ComputeFeatureInput(BaseModel):
    series_id: str
    feature_name: str


class CorrelationAnalysisInput(BaseModel):
    series_ids: list[str] = Field(description="List of FRED series IDs to analyze")
    lookback_periods: int = Field(default=52, ge=12, le=260)


class CompositeIndicatorInput(BaseModel):
    series_ids: list[str] = Field(description="List of FRED series IDs to combine")
    weights: dict[str, float] | None = Field(default=None, description="Optional weights for each series")
    lookback_periods: int = Field(default=12, ge=4, le=52)


class RegimeTransitionInput(BaseModel):
    lookback_weeks: int = Field(default=104, ge=12, le=260)


@dataclass(slots=True)
class ToolDefinition:
    name: str
    description: str
    input_model: type[BaseModel]
    runner: Callable[[BaseModel], dict[str, Any]]

    def as_openai_tool(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_model.model_json_schema(),
            },
        }


class ToolExecutor:
    def __init__(self, demo_mode: bool = True, vector_store: VectorStore | None = None) -> None:
        self.demo_mode = demo_mode
        self.fred = FredClient(demo_mode=demo_mode)
        self.kalshi = KalshiClient(demo_mode=demo_mode)
        self.polymarket = PolymarketClient(demo_mode=demo_mode)
        self.edgar = EdgarClient(demo_mode=demo_mode)
        self.news = NewsClient(demo_mode=demo_mode)
        self.vector_store = vector_store or VectorStore()
        seed_default_documents(self.vector_store)

        self.definitions: list[ToolDefinition] = [
            ToolDefinition(
                name="fred_fetch",
                description="Fetch a FRED series and return dated values.",
                input_model=FredFetchInput,
                runner=self._run_fred_fetch,
            ),
            ToolDefinition(
                name="fred_search",
                description="Search FRED series metadata by keyword query.",
                input_model=FredSearchInput,
                runner=self._run_fred_search,
            ),
            ToolDefinition(
                name="prediction_market_fetch",
                description="Fetch a prediction market contract from Kalshi or Polymarket.",
                input_model=PredictionMarketFetchInput,
                runner=self._run_prediction_market_fetch,
            ),
            ToolDefinition(
                name="edgar_fetch",
                description="Fetch a filing summary for a ticker and form type.",
                input_model=EdgarFetchInput,
                runner=self._run_edgar_fetch,
            ),
            ToolDefinition(
                name="news_fetch",
                description="Fetch recent macro news articles with sentiment.",
                input_model=NewsFetchInput,
                runner=self._run_news_fetch,
            ),
            ToolDefinition(
                name="vector_search",
                description="Search the Meridian vector memory for context.",
                input_model=VectorSearchInput,
                runner=self._run_vector_search,
            ),
            ToolDefinition(
                name="compute_feature",
                description="Compute a macro feature from a FRED series.",
                input_model=ComputeFeatureInput,
                runner=self._run_compute_feature,
            ),
            ToolDefinition(
                name="correlation_analysis",
                description="Analyze correlations between multiple FRED series to identify relationships and leading indicators.",
                input_model=CorrelationAnalysisInput,
                runner=self._run_correlation_analysis,
            ),
            ToolDefinition(
                name="composite_indicator",
                description="Build a composite indicator from multiple economic series, normalizing to z-scores and combining with optional weights.",
                input_model=CompositeIndicatorInput,
                runner=self._run_composite_indicator,
            ),
            ToolDefinition(
                name="regime_transition_probability",
                description="Estimate the probability of macro regime transition using multiple leading indicators and stress signals.",
                input_model=RegimeTransitionInput,
                runner=self._run_regime_transition_probability,
            ),
        ]

    def to_openai_tools(self) -> list[dict[str, Any]]:
        return [tool.as_openai_tool() for tool in self.definitions]

    async def execute(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        for tool in self.definitions:
            if tool.name != tool_name:
                continue
            payload = tool.input_model.model_validate(args)
            result = tool.runner(payload)
            # Round-trip to ensure JSON-serialisable output.
            json.dumps(result)
            return result
        raise KeyError(f"Unknown tool: {tool_name}")

    def _run_fred_fetch(self, payload: FredFetchInput) -> dict[str, Any]:
        series = self.fred.fetch_series(payload.series_id, payload.start_date, payload.end_date)
        observations = [
            {
                "date": row["date"].strftime("%Y-%m-%d"),
                "value": float(row["value"]),
            }
            for _, row in series.iterrows()
        ]
        return {
            "series_id": payload.series_id,
            "observations": observations,
            "count": len(observations),
        }

    def _run_fred_search(self, payload: FredSearchInput) -> dict[str, Any]:
        matches = self.fred.search(payload.query, limit=payload.limit)
        return {
            "query": payload.query,
            "results": [item.model_dump() for item in matches],
        }

    def _run_prediction_market_fetch(self, payload: PredictionMarketFetchInput) -> dict[str, Any]:
        platform = payload.platform.strip().lower()
        slug = payload.event_slug.strip().lower().replace("_", "-")

        if platform == "kalshi":
            markets = self.kalshi.get_markets()
            for market in markets:
                if slug in market.ticker.lower() or slug in market.title.lower().replace(" ", "-"):
                    output = market.model_dump()
                    output["platform"] = "kalshi"
                    return output
            raise KeyError(f"Kalshi market not found for slug: {payload.event_slug}")

        if platform == "polymarket":
            markets = self.polymarket.get_markets()
            for market in markets:
                if slug in market.condition_id.lower() or slug in market.title.lower().replace(" ", "-"):
                    output = market.model_dump()
                    output["platform"] = "polymarket"
                    return output
            raise KeyError(f"Polymarket market not found for slug: {payload.event_slug}")

        raise ValueError("platform must be either 'kalshi' or 'polymarket'")

    def _run_edgar_fetch(self, payload: EdgarFetchInput) -> dict[str, Any]:
        filing = self.edgar.get_latest_filing(payload.ticker, payload.form_type)
        return filing.model_dump()

    def _run_news_fetch(self, payload: NewsFetchInput) -> dict[str, Any]:
        articles = self.news.fetch(payload.topic, days_back=payload.days_back)
        return {
            "topic": payload.topic,
            "articles": [item.model_dump() for item in articles],
        }

    def _run_vector_search(self, payload: VectorSearchInput) -> dict[str, Any]:
        results = self.vector_store.search(payload.query, top_k=payload.top_k)
        return {
            "query": payload.query,
            "results": [
                {
                    "id": item.doc_id,
                    "text": item.text,
                    "metadata": item.metadata,
                    "score": item.score,
                }
                for item in results
            ],
        }

    def _run_compute_feature(self, payload: ComputeFeatureInput) -> dict[str, Any]:
        frame = self.fred.fetch_series(payload.series_id)
        feature = payload.feature_name.strip().lower()
        if feature == "yield_curve_slope":
            return yield_curve_slope(frame)
        if feature == "inflation_momentum":
            return inflation_momentum(frame)
        if feature == "credit_stress":
            return credit_stress(frame)
        if feature == "monetary_regime":
            return monetary_regime(frame)
        raise ValueError(f"Unsupported feature_name: {payload.feature_name}")

    def _run_correlation_analysis(self, payload: CorrelationAnalysisInput) -> dict[str, Any]:
        series_dict = {}
        for series_id in payload.series_ids:
            series_dict[series_id] = self.fred.fetch_series(series_id)
        return cross_series_correlation(series_dict, lookback_periods=payload.lookback_periods)

    def _run_composite_indicator(self, payload: CompositeIndicatorInput) -> dict[str, Any]:
        series_dict = {}
        for series_id in payload.series_ids:
            series_dict[series_id] = self.fred.fetch_series(series_id)
        return composite_indicator(series_dict, weights=payload.weights, lookback_periods=payload.lookback_periods)

    def _run_regime_transition_probability(self, payload: RegimeTransitionInput) -> dict[str, Any]:
        # Fetch all key series for regime analysis
        series_dict = {
            "T10Y2Y": self.fred.fetch_series("T10Y2Y"),
            "CPIAUCSL": self.fred.fetch_series("CPIAUCSL"),
            "FEDFUNDS": self.fred.fetch_series("FEDFUNDS"),
            "BAMLH0A0HYM2": self.fred.fetch_series("BAMLH0A0HYM2"),
            "UNRATE": self.fred.fetch_series("UNRATE"),
        }
        return regime_transition_probability(series_dict, lookback_weeks=payload.lookback_weeks)
