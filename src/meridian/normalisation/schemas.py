from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class DataPoint(BaseModel):
    date: str
    value: float


class CanonicalMarket(BaseModel):
    id: str
    platform: Literal["kalshi", "polymarket"]
    title: str
    category: str
    resolution_date: str
    market_probability: float = Field(ge=0.0, le=1.0)
    volume_usd: float = Field(ge=0.0)
    open_interest: float = Field(ge=0.0)
    last_updated: str
    history: list[DataPoint] = Field(default_factory=list)


class BriefPoint(BaseModel):
    point: str
    source_ref: str

    @field_validator("source_ref")
    @classmethod
    def ensure_source_ref(cls, value: str) -> str:
        if ":" not in value:
            raise ValueError("source_ref must follow tool_name:id format")
        return value


class RiskPoint(BaseModel):
    risk: str
    source_ref: str

    @field_validator("source_ref")
    @classmethod
    def ensure_source_ref(cls, value: str) -> str:
        if ":" not in value:
            raise ValueError("source_ref must follow tool_name:id format")
        return value


class SourceRef(BaseModel):
    type: Literal["fred", "edgar", "news", "market"]
    id: str
    excerpt: str
    claim_refs: list[str] = Field(default_factory=list)
    preview: dict[str, Any] | None = None


class ResearchBrief(BaseModel):
    question: str
    query_class: Literal["macro_outlook", "event_probability", "ticker_macro"] | None = None
    follow_up_context: str | None = None
    thesis: str
    bull_case: list[BriefPoint]
    bear_case: list[BriefPoint]
    key_risks: list[RiskPoint]
    confidence: int = Field(ge=1, le=5)
    confidence_rationale: str
    methodology_summary: str | None = None
    sources: list[SourceRef]
    created_at: str
    trace_steps: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def enforce_case_lengths(self) -> "ResearchBrief":
        if not 3 <= len(self.bull_case) <= 5:
            raise ValueError("bull_case must contain 3-5 items")
        if not 2 <= len(self.bear_case) <= 5:
            raise ValueError("bear_case must contain 2-5 items")
        if len(self.key_risks) < 2:
            raise ValueError("key_risks must contain at least 2 items")
        return self


class TraceStep(BaseModel):
    step_index: int = Field(ge=0)
    type: Literal["tool_call", "tool_result", "reasoning", "brief_delta", "complete", "error", "reflection"]
    tool_name: str | None = None
    tool_args: dict | None = None
    content: str | dict | list | None = None
    timestamp: str

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value


class MispricingScore(BaseModel):
    market_id: str
    market_prob: float = Field(ge=0.0, le=1.0)
    model_prob: float = Field(ge=0.0, le=1.0)
    dislocation: float = Field(ge=0.0, le=1.0)
    direction: Literal["market_overpriced", "market_underpriced"]
    explanation: str
    confidence: int = Field(ge=1, le=5)
    scored_at: str
