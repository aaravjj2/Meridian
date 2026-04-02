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
- `bull_case: list[{ point, source_ref }]` (3-5)
- `bear_case: list[{ point, source_ref }]` (2-5)
- `key_risks: list[{ risk, source_ref }]` (>=2)
- `confidence: int [1, 5]`
- `confidence_rationale: str`
- `sources: list[{ type, id, excerpt }]`
- `created_at: str (ISO)`
- `trace_steps: list[int]`

## TraceStep

- `step_index: int`
- `type: tool_call | tool_result | reasoning | brief_delta | complete | error`
- `tool_name?: str`
- `tool_args?: dict`
- `content?: str | dict | list`
- `timestamp: str (ISO)`

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
