from __future__ import annotations

from meridian.normalisation.schemas import ResearchTemplateDefinition, ResearchTemplateId


_TEMPLATE_CATALOG: tuple[ResearchTemplateDefinition, ...] = (
    ResearchTemplateDefinition(
        id="macro_outlook",
        title="Macro outlook",
        description="Build a balanced macro baseline with explicit bull, bear, and risk structure.",
        framing="Start from cycle position, inflation trend, and policy stance before sizing risk.",
        query_class_default="macro_outlook",
        emphasis=[
            "Cycle and regime interpretation",
            "Cross-check inflation, growth, and credit",
            "Translate evidence into scenario odds",
        ],
        evaluation_expectations=[
            "At least one macro signal conflict is surfaced",
            "Freshness and snapshot provenance checks pass",
        ],
    ),
    ResearchTemplateDefinition(
        id="event_probability_interpretation",
        title="Event probability interpretation",
        description="Interpret market-implied event odds against macro evidence and policy context.",
        framing="Start from priced probabilities, then test whether macro inputs justify that pricing.",
        query_class_default="event_probability",
        emphasis=[
            "Cross-venue probability consistency",
            "Macro validation of priced odds",
            "Repricing and communication tail risks",
        ],
        evaluation_expectations=[
            "Event-odds claims map to market sources",
            "Confidence rationale discusses timing risk",
        ],
    ),
    ResearchTemplateDefinition(
        id="ticker_macro_framing",
        title="Ticker + macro framing",
        description="Blend single-name or sector positioning with macro and credit regime overlays.",
        framing="Combine bottom-up fundamental context with top-down macro risk budgeting.",
        query_class_default="ticker_macro",
        emphasis=[
            "Fundamental versus macro tension",
            "Credit and policy sensitivity",
            "Positioning risk controls",
        ],
        evaluation_expectations=[
            "Thesis references both ticker and macro evidence",
            "Conflict section captures bottom-up vs top-down tension",
        ],
    ),
    ResearchTemplateDefinition(
        id="thesis_change_compare",
        title="Compare old vs new thesis",
        description="Update or challenge a prior thesis and make deltas explicit for auditability.",
        framing="Anchor on prior thesis context, then highlight what changed and why.",
        query_class_default="macro_outlook",
        emphasis=[
            "Prior-vs-current thesis deltas",
            "Evidence that changed confidence",
            "Explicit conflict and risk updates",
        ],
        evaluation_expectations=[
            "Follow-up context is present when available",
            "Delta-oriented reasoning is reflected in thesis narrative",
        ],
    ),
)

_TEMPLATE_INDEX: dict[ResearchTemplateId, ResearchTemplateDefinition] = {
    item.id: item for item in _TEMPLATE_CATALOG
}


def infer_template_id(question: str) -> ResearchTemplateId:
    lowered = question.lower()
    upper = question.upper()

    ticker_tokens = {
        "AAPL",
        "MSFT",
        "NVDA",
        "TSLA",
        "AMZN",
        "META",
        "GOOGL",
        "XLF",
        "XLK",
        "XLE",
        "SMH",
    }
    if any(token in upper for token in ticker_tokens) or "ticker" in lowered or "sector" in lowered:
        return "ticker_macro_framing"

    probability_markers = ["probability", "odds", "chance", "implied", "priced", "event"]
    if any(marker in lowered for marker in probability_markers):
        return "event_probability_interpretation"

    return "macro_outlook"


def list_research_templates() -> list[ResearchTemplateDefinition]:
    return [item.model_copy(deep=True) for item in _TEMPLATE_CATALOG]


def resolve_research_template(template_id: str | None, question: str | None = None) -> ResearchTemplateDefinition:
    if template_id in _TEMPLATE_INDEX:
        return _TEMPLATE_INDEX[template_id].model_copy(deep=True)
    if question:
        inferred = infer_template_id(question)
        return _TEMPLATE_INDEX[inferred].model_copy(deep=True)
    return _TEMPLATE_INDEX["macro_outlook"].model_copy(deep=True)


def template_prompt_hint(template: ResearchTemplateDefinition) -> str:
    emphasis = "; ".join(template.emphasis)
    return (
        f"Research template: {template.id} ({template.title}). "
        f"Framing: {template.framing}. Emphasis: {emphasis}."
    )
