# Meridian Schemas

## CanonicalMarket

- `id: str`
- `platform: "kalshi" | "polymarket"`
- `title: str`
- `category: str`
- `resolution_date: str (ISO)`
- `market_probability: float [0, 1]`
- `volume_usd: float`
- `open_interest: float`
- `last_updated: str (ISO)`
- `history: list[DataPoint]`

## ResearchBrief

- `question: str`
- `thesis: str`
- `bull_case: list[{ claim_id, point, source_ref }]` (3-5)
- `bear_case: list[{ claim_id, point, source_ref }]` (2-5)
- `key_risks: list[{ claim_id, risk, source_ref }]` (>=2)
- `confidence: int [1, 5]`
- `confidence_rationale: str`
- `sources: list[{ type, id, excerpt, claim_refs?, preview? }]`
- `signal_conflicts: list[{ conflict_id, title, summary, severity, claim_refs, source_refs }]`
- `created_at: str (ISO)`
- `trace_steps: list[int]`

Validation notes:

- `claim_id` values are unique across bull/bear/risk sections.
- Every claim must be linked from at least one `sources[].claim_refs` entry.
- `signal_conflicts[].claim_refs` must reference valid `claim_id` values.
- `signal_conflicts[].source_refs` uses `type:id` format (example: `fred:T10Y2Y`).

## TraceStep

- `step_index: int`
- `type: tool_call | tool_result | reasoning | brief_delta | complete | error`
- `tool_name?: str`
- `tool_args?: dict`
- `content?: str | dict | list`
- `timestamp: str (ISO)`

## SavedResearchSession

- `id: str` (stable saved-session identifier)
- `question: str`
- `mode: "demo" | "live"`
- `session_id: str` (runtime research-thread id used for follow-ups)
- `query_class: "macro_outlook" | "event_probability" | "ticker_macro" | null`
- `follow_up_context: str | null`
- `brief: ResearchBrief`
- `trace_events: list[SavedTraceEvent]`
- `evidence_state: { active_claim_id, expanded_source_id } | null`
- `created_at: str (ISO)`
- `saved_at: str (ISO)`
- `updated_at: str (ISO)`
- `canonical_signature: str` (SHA256 of canonical content for deterministic audit checks)

## MispricingScore

- `market_id: str`
- `market_prob: float [0,1]`
- `model_prob: float [0,1]`
- `dislocation: float [0,1]`
- `direction: market_overpriced | market_underpriced`
- `explanation: str`
- `confidence: int [1,5]`
- `scored_at: str (ISO)`

## features.json snapshot

- `yield_curve_current`
- `yield_curve_delta_3m`
- `sahm_gap`
- `recession_signal`
- `inflation_3m_annualized_pct`
- `credit_spread`
- `credit_stress_z`
- `fed_funds`
- `monetary_regime`
- `regime_growth`
- `regime_inflation`
- `regime_monetary`
- `regime_credit`
- `regime_labor`
