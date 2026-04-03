from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, AsyncGenerator

import httpx

from meridian.agent.prompt import build_system_prompt
from meridian.agent.tools import ToolExecutor
from meridian.normalisation.schemas import ResearchBrief, TraceStep
from meridian.settings import FIXTURES_DIR, is_demo_mode


logger = logging.getLogger(__name__)


def _iso_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _extract_json_payload(content: str) -> dict[str, Any] | None:
    stripped = content.strip()
    if not stripped:
        return None
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        parsed = json.loads(stripped[start : end + 1])
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        return None
    return None


class ResearchAgent:
    def __init__(
        self,
        demo_mode: bool | None = None,
        demo_delay_seconds: float = 0.08,
        max_tool_calls: int = 25,
        trace_path: Path | None = None,
        tool_executor: ToolExecutor | None = None,
        enable_reflection: bool = True,
        reflection_interval: int = 5,
    ) -> None:
        self.demo_mode = is_demo_mode() if demo_mode is None else demo_mode
        self.demo_delay_seconds = demo_delay_seconds
        self.max_tool_calls = max_tool_calls
        self.trace_path = trace_path or (FIXTURES_DIR / "traces" / "demo_trace.json")
        self.tools = tool_executor or ToolExecutor(demo_mode=self.demo_mode)
        self.enable_reflection = enable_reflection
        self.reflection_interval = reflection_interval
        self.tools_called: list[str] = []

    async def call_glm(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]], stream: bool = True) -> httpx.Response:
        api_key = os.getenv("ZAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("ZAI_API_KEY is required for live mode")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "glm-5.1",
                    "messages": messages,
                    "tools": tools,
                    "stream": stream,
                    "max_tokens": 4096,
                },
                timeout=120.0,
            )
        response.raise_for_status()
        return response

    async def run(self, question: str, mode: str | None = None) -> AsyncGenerator[TraceStep, None]:
        async for step in self.run_with_context(question=question, mode=mode, session_context=None):
            yield step

    async def run_with_context(
        self,
        question: str,
        mode: str | None = None,
        session_context: dict[str, Any] | None = None,
    ) -> AsyncGenerator[TraceStep, None]:
        resolved_mode = (mode or ("demo" if self.demo_mode else "live")).strip().lower()
        if resolved_mode == "demo":
            async for step in self._run_demo(question, session_context=session_context):
                yield step
            return

        async for step in self._run_live(question, session_context=session_context):
            yield step

    def _classify_query(self, question: str) -> str:
        lowered = question.lower()
        upper = question.upper()

        ticker_tokens = [
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
            "XLI",
            "SMH",
        ]
        if any(token in upper for token in ticker_tokens):
            return "ticker_macro"
        if "ticker" in lowered or "sector" in lowered or "industry" in lowered:
            return "ticker_macro"

        event_markers = [
            "probability",
            "odds",
            "chance",
            "implied",
            "priced",
            "pricing",
            "event",
        ]
        if any(marker in lowered for marker in event_markers):
            return "event_probability"

        return "macro_outlook"

    def _session_follow_up_note(self, session_context: dict[str, Any] | None) -> str | None:
        if not session_context:
            return None
        prior_question = str(session_context.get("last_question", "")).strip()
        prior_thesis = str(session_context.get("last_thesis", "")).strip()
        if not prior_question:
            return None
        note = f"Follow-up to prior question: {prior_question}"
        if prior_thesis:
            note += f" | Prior thesis: {prior_thesis}"
        return note

    def _fred_preview(self, series_id: str) -> dict[str, Any]:
        try:
            frame = self.tools.fred.fetch_series(series_id)
        except Exception:
            return {"kind": "fred_series", "series_id": series_id, "points": []}

        if frame.empty:
            return {"kind": "fred_series", "series_id": series_id, "points": []}

        points = []
        for _, row in frame.tail(6).iterrows():
            points.append(
                {
                    "date": row["date"].strftime("%Y-%m-%d"),
                    "value": round(float(row["value"]), 4),
                }
            )

        latest = points[-1]["value"]
        baseline = points[0]["value"]
        delta_lookback = round(latest - baseline, 4)

        return {
            "kind": "fred_series",
            "series_id": series_id,
            "latest": latest,
            "delta_lookback": delta_lookback,
            "points": points,
        }

    def _market_preview(self, market_id: str) -> dict[str, Any]:
        snapshot_path = FIXTURES_DIR / "screener_snapshot.json"
        try:
            payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
            contracts = payload.get("contracts", [])
            for contract in contracts:
                if contract.get("market_id") == market_id:
                    return {
                        "kind": "market_contract",
                        "market_id": contract.get("market_id"),
                        "platform": contract.get("platform"),
                        "market_prob": contract.get("market_prob"),
                        "model_prob": contract.get("model_prob"),
                        "dislocation": contract.get("dislocation"),
                        "resolution_date": contract.get("resolution_date"),
                        "confidence": contract.get("confidence"),
                    }
        except Exception:
            pass
        return {
            "kind": "market_contract",
            "market_id": market_id,
        }

    def _news_preview(self, topic_slug: str) -> dict[str, Any]:
        path = FIXTURES_DIR / "news" / f"{topic_slug}.json"
        try:
            records = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {"kind": "news_digest", "topic": topic_slug, "headlines": []}

        headlines = [str(item.get("title", "")) for item in records[:3] if item.get("title")]
        snippets = [str(item.get("snippet", "")) for item in records[:2] if item.get("snippet")]
        return {
            "kind": "news_digest",
            "topic": topic_slug,
            "headlines": headlines,
            "snippets": snippets,
            "count": len(records),
        }

    def _edgar_preview(self, ticker: str, form_type: str) -> dict[str, Any]:
        try:
            filing = self.tools.edgar.get_latest_filing(ticker=ticker, form_type=form_type)
            return {
                "kind": "filing_summary",
                "ticker": filing.ticker,
                "form_type": filing.form_type,
                "filed_date": filing.filed_date,
                "accession_number": filing.accession_number,
                "highlights": filing.text_chunks[:3],
            }
        except Exception:
            return {
                "kind": "filing_summary",
                "ticker": ticker,
                "form_type": form_type,
                "highlights": [],
            }

    def _build_demo_brief(
        self,
        question: str,
        query_class: str,
        follow_up_note: str | None,
        trace_steps: list[int],
        created_at: str,
    ) -> dict[str, Any]:
        if query_class == "event_probability":
            return {
                "question": question,
                "query_class": query_class,
                "follow_up_context": follow_up_note,
                "thesis": "Event probabilities are pricing a relatively fast easing path, but macro cross-checks suggest the market is slightly ahead of the underlying policy reaction function.",
                "bull_case": [
                    {
                        "claim_id": "bull-1-fed-cut-cross-venue",
                        "point": "Both major market venues imply elevated cut probabilities, reinforcing near-term easing expectations.",
                        "source_ref": "prediction_market_fetch:pm-fed-cut-june-2026",
                    },
                    {
                        "claim_id": "bull-2-cpi-cooling-trend",
                        "point": "Recent inflation prints are cooling directionally, which supports policy flexibility.",
                        "source_ref": "fred_fetch:CPIAUCSL",
                    },
                    {
                        "claim_id": "bull-3-fed-guidance-data-dependent",
                        "point": "Fed communication has remained data-dependent rather than outright restrictive.",
                        "source_ref": "news_fetch:fed-rate-decision",
                    },
                ],
                "bear_case": [
                    {
                        "claim_id": "bear-1-policy-rate-stays-restrictive",
                        "point": "Current policy levels remain restrictive and could stay elevated if inflation progress stalls.",
                        "source_ref": "fred_fetch:FEDFUNDS",
                    },
                    {
                        "claim_id": "bear-2-probability-mean-reversion",
                        "point": "Market-implied probabilities can mean-revert quickly around high-impact data releases.",
                        "source_ref": "prediction_market_fetch:KXFEDCUT-H1-2026",
                    },
                ],
                "key_risks": [
                    {
                        "claim_id": "risk-1-inflation-reacceleration",
                        "risk": "A surprise inflation re-acceleration could invalidate easing-heavy event pricing.",
                        "source_ref": "fred_fetch:CPIAUCSL",
                    },
                    {
                        "claim_id": "risk-2-fomc-communication-volatility",
                        "risk": "Positioning asymmetry can amplify repricing volatility around FOMC communication.",
                        "source_ref": "news_fetch:fed-rate-decision",
                    },
                ],
                "confidence": 3,
                "confidence_rationale": "Pricing and macro signals broadly align but timing risk around policy communication remains meaningful.",
                "methodology_summary": "Compared cross-venue event pricing with inflation and policy-level context, then stress-tested the interpretation against recent policy communication.",
                "sources": [
                    {
                        "type": "market",
                        "id": "pm-fed-cut-june-2026",
                        "excerpt": "Polymarket implies an elevated probability of at least a 50bp cut by mid-2026.",
                        "claim_refs": ["bull-1-fed-cut-cross-venue", "bear-2-probability-mean-reversion"],
                        "preview": self._market_preview("pm-fed-cut-june-2026"),
                    },
                    {
                        "type": "market",
                        "id": "KXFEDCUT-H1-2026",
                        "excerpt": "Kalshi pricing is directionally consistent with elevated easing expectations.",
                        "claim_refs": ["bull-1-fed-cut-cross-venue", "bear-2-probability-mean-reversion"],
                        "preview": self._market_preview("KXFEDCUT-H1-2026"),
                    },
                    {
                        "type": "fred",
                        "id": "FEDFUNDS",
                        "excerpt": "Policy rate level remains restrictive versus long-run neutral assumptions.",
                        "claim_refs": ["bear-1-policy-rate-stays-restrictive"],
                        "preview": self._fred_preview("FEDFUNDS"),
                    },
                    {
                        "type": "fred",
                        "id": "CPIAUCSL",
                        "excerpt": "Inflation trajectory has cooled but still requires confirmation across future prints.",
                        "claim_refs": ["bull-2-cpi-cooling-trend", "risk-1-inflation-reacceleration"],
                        "preview": self._fred_preview("CPIAUCSL"),
                    },
                    {
                        "type": "news",
                        "id": "fed-rate-decision",
                        "excerpt": "Recent coverage emphasizes a data-dependent easing posture.",
                        "claim_refs": ["bull-3-fed-guidance-data-dependent", "risk-2-fomc-communication-volatility"],
                        "preview": self._news_preview("fed-rate-decision"),
                    },
                ],
                "signal_conflicts": [
                    {
                        "conflict_id": "conflict-event-pricing-timing",
                        "title": "Event Pricing Versus Timing Risk",
                        "summary": "Cross-venue odds support easing, but historical repricing around macro releases argues for timing caution.",
                        "severity": "medium",
                        "claim_refs": ["bull-1-fed-cut-cross-venue", "bear-2-probability-mean-reversion"],
                        "source_refs": ["market:pm-fed-cut-june-2026", "market:KXFEDCUT-H1-2026"],
                    },
                    {
                        "conflict_id": "conflict-disinflation-tail-risk",
                        "title": "Disinflation Progress Versus Inflation Tail Risk",
                        "summary": "The same CPI trend supports baseline easing while still leaving room for a hawkish surprise path.",
                        "severity": "high",
                        "claim_refs": ["bull-2-cpi-cooling-trend", "risk-1-inflation-reacceleration"],
                        "source_refs": ["fred:CPIAUCSL"],
                    },
                ],
                "created_at": created_at,
                "trace_steps": trace_steps,
            }

        if query_class == "ticker_macro":
            return {
                "question": question,
                "query_class": query_class,
                "follow_up_context": follow_up_note,
                "thesis": "Ticker-and-macro framing points to a quality bias: company fundamentals can hold if growth decelerates gradually, but spread and recession signals argue for tighter risk control.",
                "bull_case": [
                    {
                        "claim_id": "bull-1-services-margin-resilience",
                        "point": "Recent filing commentary indicates durable services and margin resilience despite macro headwinds.",
                        "source_ref": "edgar_fetch:AAPL_10-K",
                    },
                    {
                        "claim_id": "bull-2-real-growth-positive",
                        "point": "Real activity remains positive, reducing immediate hard-landing pressure on broad earnings.",
                        "source_ref": "fred_fetch:GDPC1",
                    },
                    {
                        "claim_id": "bull-3-easing-supports-duration",
                        "point": "Macro easing probabilities can support valuation duration for high-quality equities.",
                        "source_ref": "prediction_market_fetch:pm-fed-cut-june-2026",
                    },
                ],
                "bear_case": [
                    {
                        "claim_id": "bear-1-credit-spread-stress",
                        "point": "High-yield spread levels still indicate non-trivial financing stress beneath index-level stability.",
                        "source_ref": "fred_fetch:BAMLH0A0HYM2",
                    },
                    {
                        "claim_id": "bear-2-recession-pricing-elevated",
                        "point": "Recession-event pricing remains elevated enough to pressure cyclical sectors if growth slips.",
                        "source_ref": "prediction_market_fetch:pm-recession-2026",
                    },
                ],
                "key_risks": [
                    {
                        "claim_id": "risk-1-macro-shock-overwhelms-fundamentals",
                        "risk": "Macro shocks can overwhelm single-name fundamentals over short windows.",
                        "source_ref": "news_fetch:recession-risk",
                    },
                    {
                        "claim_id": "risk-2-credit-volatility-compresses-multiples",
                        "risk": "Credit or policy volatility can compress multiples even if earnings remain intact.",
                        "source_ref": "fred_fetch:BAMLH0A0HYM2",
                    },
                ],
                "confidence": 3,
                "confidence_rationale": "Fundamental resilience and macro caution are both credible, producing a balanced but not high-conviction stance.",
                "methodology_summary": "Combined filing-level fundamental context with macro growth, credit, and event-pricing signals to frame ticker risk/reward under current regime conditions.",
                "sources": [
                    {
                        "type": "edgar",
                        "id": "AAPL_10-K",
                        "excerpt": "Latest filing highlights services resilience, margin durability, and sensitivity to financing conditions.",
                        "claim_refs": ["bull-1-services-margin-resilience"],
                        "preview": self._edgar_preview("AAPL", "10-K"),
                    },
                    {
                        "type": "fred",
                        "id": "GDPC1",
                        "excerpt": "Real GDP trend remains positive, supporting a slower-growth rather than immediate-contraction baseline.",
                        "claim_refs": ["bull-2-real-growth-positive"],
                        "preview": self._fred_preview("GDPC1"),
                    },
                    {
                        "type": "fred",
                        "id": "BAMLH0A0HYM2",
                        "excerpt": "Credit spreads remain above low-stress ranges and warrant risk budgeting discipline.",
                        "claim_refs": ["bear-1-credit-spread-stress", "risk-2-credit-volatility-compresses-multiples"],
                        "preview": self._fred_preview("BAMLH0A0HYM2"),
                    },
                    {
                        "type": "market",
                        "id": "pm-fed-cut-june-2026",
                        "excerpt": "Cut-probability pricing supports duration-sensitive valuation cohorts.",
                        "claim_refs": ["bull-3-easing-supports-duration"],
                        "preview": self._market_preview("pm-fed-cut-june-2026"),
                    },
                    {
                        "type": "market",
                        "id": "pm-recession-2026",
                        "excerpt": "Recession probability is still materially priced, especially for cyclical sensitivity.",
                        "claim_refs": ["bear-2-recession-pricing-elevated", "risk-1-macro-shock-overwhelms-fundamentals"],
                        "preview": self._market_preview("pm-recession-2026"),
                    },
                    {
                        "type": "news",
                        "id": "recession-risk",
                        "excerpt": "Recent headlines highlight mixed growth resilience versus financing fragility.",
                        "claim_refs": ["risk-1-macro-shock-overwhelms-fundamentals"],
                        "preview": self._news_preview("recession-risk"),
                    },
                ],
                "signal_conflicts": [
                    {
                        "conflict_id": "conflict-fundamentals-vs-credit",
                        "title": "Fundamental Durability Versus Credit Tightness",
                        "summary": "Issuer-level resilience is credible, but spread stress can still compress valuations before fundamentals deteriorate.",
                        "severity": "high",
                        "claim_refs": [
                            "bull-1-services-margin-resilience",
                            "bear-1-credit-spread-stress",
                            "risk-2-credit-volatility-compresses-multiples",
                        ],
                        "source_refs": ["edgar:AAPL_10-K", "fred:BAMLH0A0HYM2"],
                    },
                    {
                        "conflict_id": "conflict-growth-vs-recession-pricing",
                        "title": "Growth Baseline Versus Recession Pricing",
                        "summary": "Positive real activity data and elevated recession pricing point to a non-trivial distribution of outcomes.",
                        "severity": "medium",
                        "claim_refs": [
                            "bull-2-real-growth-positive",
                            "bear-2-recession-pricing-elevated",
                            "risk-1-macro-shock-overwhelms-fundamentals",
                        ],
                        "source_refs": ["fred:GDPC1", "market:pm-recession-2026", "news:recession-risk"],
                    },
                ],
                "created_at": created_at,
                "trace_steps": trace_steps,
            }

        return {
            "question": question,
            "query_class": "macro_outlook",
            "follow_up_context": follow_up_note,
            "thesis": "Macro conditions indicate a late-cycle regime: growth is still positive, disinflation is progressing, and credit remains watchful rather than crisis-like.",
            "bull_case": [
                {
                    "claim_id": "bull-1-inversion-easing",
                    "point": "Yield-curve inversion has eased from prior extremes, reducing immediate breakdown risk.",
                    "source_ref": "fred_fetch:T10Y2Y",
                },
                {
                    "claim_id": "bull-2-disinflation-progress",
                    "point": "Inflation momentum has moderated, supporting policy-flexibility scenarios.",
                    "source_ref": "fred_fetch:CPIAUCSL",
                },
                {
                    "claim_id": "bull-3-easing-pricing-support",
                    "point": "Rate-cut pricing remains supportive for risk appetite if growth stays resilient.",
                    "source_ref": "prediction_market_fetch:KXFEDCUT-H1-2026",
                },
            ],
            "bear_case": [
                {
                    "claim_id": "bear-1-inversion-still-warning",
                    "point": "Inversion remains present and historically consistent with lagged growth pressure.",
                    "source_ref": "fred_fetch:T10Y2Y",
                },
                {
                    "claim_id": "bear-2-credit-stress-elevated",
                    "point": "Credit stress is contained but still elevated relative to low-volatility regimes.",
                    "source_ref": "fred_fetch:BAMLH0A0HYM2",
                },
            ],
            "key_risks": [
                {
                    "claim_id": "risk-1-inflation-reacceleration",
                    "risk": "Re-acceleration in inflation can tighten policy expectations and financial conditions.",
                    "source_ref": "fred_fetch:CPIAUCSL",
                },
                {
                    "claim_id": "risk-2-policy-communication-repricing",
                    "risk": "Event repricing around policy communication can quickly widen macro uncertainty.",
                    "source_ref": "news_fetch:fed-rate-decision",
                },
            ],
            "confidence": 3,
            "confidence_rationale": "Evidence is cross-validated but mixed, favoring balanced positioning over high-conviction directional calls.",
            "methodology_summary": "Cross-checked yield-curve, inflation, credit, event-pricing, and news signals, then synthesized directional consistency and tail-risk factors.",
            "sources": [
                {
                    "type": "fred",
                    "id": "T10Y2Y",
                    "excerpt": "Curve inversion is still negative but less severe than recent lows.",
                    "claim_refs": ["bull-1-inversion-easing", "bear-1-inversion-still-warning"],
                    "preview": self._fred_preview("T10Y2Y"),
                },
                {
                    "type": "fred",
                    "id": "CPIAUCSL",
                    "excerpt": "Inflation level remains high but direction has moderated.",
                    "claim_refs": ["bull-2-disinflation-progress", "risk-1-inflation-reacceleration"],
                    "preview": self._fred_preview("CPIAUCSL"),
                },
                {
                    "type": "fred",
                    "id": "BAMLH0A0HYM2",
                    "excerpt": "HY spread regime suggests caution rather than systemic stress.",
                    "claim_refs": ["bear-2-credit-stress-elevated"],
                    "preview": self._fred_preview("BAMLH0A0HYM2"),
                },
                {
                    "type": "market",
                    "id": "KXFEDCUT-H1-2026",
                    "excerpt": "Kalshi event pricing supports an easing-biased rates path.",
                    "claim_refs": ["bull-3-easing-pricing-support"],
                    "preview": self._market_preview("KXFEDCUT-H1-2026"),
                },
                {
                    "type": "news",
                    "id": "fed-rate-decision",
                    "excerpt": "Recent macro-news flow emphasizes data-dependent policy and two-sided recession hedging.",
                    "claim_refs": ["risk-2-policy-communication-repricing"],
                    "preview": self._news_preview("fed-rate-decision"),
                },
            ],
            "signal_conflicts": [
                {
                    "conflict_id": "conflict-curve-interpretation",
                    "title": "Curve Improvement Versus Residual Inversion",
                    "summary": "The slope has improved from extremes while still remaining in a historically cautious range.",
                    "severity": "medium",
                    "claim_refs": ["bull-1-inversion-easing", "bear-1-inversion-still-warning"],
                    "source_refs": ["fred:T10Y2Y"],
                },
                {
                    "conflict_id": "conflict-disinflation-vs-tail-risk",
                    "title": "Disinflation Baseline Versus Hawkish Tail",
                    "summary": "Cooling inflation supports easing scenarios, but communication shocks can still shift policy expectations abruptly.",
                    "severity": "high",
                    "claim_refs": [
                        "bull-2-disinflation-progress",
                        "risk-1-inflation-reacceleration",
                        "risk-2-policy-communication-repricing",
                    ],
                    "source_refs": ["fred:CPIAUCSL", "news:fed-rate-decision"],
                },
            ],
            "created_at": created_at,
            "trace_steps": trace_steps,
        }

    def _demo_reasoning_texts(self, query_class: str, follow_up_note: str | None) -> list[str]:
        follow_up_text = follow_up_note or "No prior context in this session; using baseline macro evidence path."
        if query_class == "event_probability":
            return [
                "Classified query as event-probability interpretation. Prioritizing market-implied odds, policy-rate context, and inflation trend confirmation.",
                "Cross-venue pricing is directionally consistent; now checking whether macro conditions justify current event odds or imply overextension.",
                f"Synthesizing event-odds interpretation with macro constraints. {follow_up_text}",
            ]
        if query_class == "ticker_macro":
            return [
                "Classified query as ticker-plus-macro framing. Combining filing-level fundamentals with regime and credit evidence.",
                "Macro regime and spread conditions are being used as risk-budget overlays on the single-name or sector thesis.",
                f"Combining bottom-up and top-down signals into a balanced trade framing. {follow_up_text}",
            ]
        return [
            "Classified query as macro outlook. Pulling term structure, inflation, credit, and event-pricing signals for a balanced directional view.",
            "Evidence remains mixed but coherent enough for scenario framing; now translating into explicit bull/bear/risk structure.",
            f"Final macro synthesis with explicit confidence guardrails. {follow_up_text}",
        ]

    def _brief_delta_text(self, brief: dict[str, Any], section: str) -> str:
        if section == "thesis":
            return str(brief.get("thesis", ""))
        if section == "bull_case":
            points = brief.get("bull_case", [])
            if points:
                return str(points[0].get("point", ""))
        if section == "bear_case":
            points = brief.get("bear_case", [])
            if points:
                return str(points[0].get("point", ""))
        if section == "key_risks":
            risks = brief.get("key_risks", [])
            if risks:
                return str(risks[0].get("risk", ""))
        return "Section updated."

    async def _run_demo(
        self,
        question: str,
        session_context: dict[str, Any] | None = None,
    ) -> AsyncGenerator[TraceStep, None]:
        """
        Run the research agent in demo mode using a pre-recorded trace file.

        Args:
            question: The user's research question (not used in demo mode, but preserved for trace)

        Yields:
            TraceStep: Trace steps from the demo trace file

        The demo mode loads a pre-recorded research trace from JSON and replays it
        with timing to simulate real-time execution. This is used for demonstrations
        and testing without making live API calls.
        """
        # Check trace file existence
        if not self.trace_path.exists():
            logger.error(f"Demo trace file not found: {self.trace_path}")
            yield TraceStep(
                step_index=0,
                type="error",
                content=f"Demo trace file not found: {self.trace_path}. "
                f"Please ensure demo fixtures are properly installed.",
                timestamp=_iso_now(),
            )
            return

        # Read and validate trace file
        try:
            trace_content = self.trace_path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.error(f"Failed to read demo trace file: {exc}")
            yield TraceStep(
                step_index=0,
                type="error",
                content=f"Failed to read demo trace file: {exc}",
                timestamp=_iso_now(),
            )
            return

        # Parse JSON with error handling
        try:
            payload = json.loads(trace_content)
        except json.JSONDecodeError as exc:
            logger.error(f"Demo trace file contains invalid JSON: {exc}")
            yield TraceStep(
                step_index=0,
                type="error",
                content=f"Demo trace file contains invalid JSON: {exc}. "
                f"Error at line {exc.lineno}, column {exc.colno}",
                timestamp=_iso_now(),
            )
            return

        # Validate payload structure
        if not isinstance(payload, list):
            logger.error(f"Demo trace payload must be a JSON array, got: {type(payload).__name__}")
            yield TraceStep(
                step_index=0,
                type="error",
                content="Demo trace payload must be a JSON array of trace events. "
                f"Got: {type(payload).__name__}",
                timestamp=_iso_now(),
            )
            return

        if not payload:
            logger.warning("Demo trace file is empty")
            yield TraceStep(
                step_index=0,
                type="error",
                content="Demo trace file is empty. Cannot replay demo research.",
                timestamp=_iso_now(),
            )
            return

        query_class = self._classify_query(question)
        follow_up_note = self._session_follow_up_note(session_context)
        complete_index = 0
        for idx, raw in enumerate(payload):
            if str(raw.get("type", "")) == "complete":
                complete_index = int(raw.get("step", idx))
                break
        trace_steps = list(range(complete_index + 1))
        created_at = str(payload[-1].get("ts", _iso_now()))
        demo_brief = self._build_demo_brief(
            question=question,
            query_class=query_class,
            follow_up_note=follow_up_note,
            trace_steps=trace_steps,
            created_at=created_at,
        )
        reasoning_texts = self._demo_reasoning_texts(query_class=query_class, follow_up_note=follow_up_note)
        reasoning_idx = 0

        # Replay trace with timing
        for idx, raw in enumerate(payload):
            try:
                await asyncio.sleep(self.demo_delay_seconds)
                event = dict(raw)
                event_type = str(event.get("type", "reasoning"))
                step_index = int(event.get("step", idx))
                timestamp = str(event.get("ts", _iso_now()))

                tool_name = event.get("tool")
                tool_args = event.get("args")
                content: Any = event.get("content")

                if event_type == "tool_result":
                    content = {"preview": event.get("preview", [])}
                elif event_type == "reasoning":
                    default_text = str(event.get("text", ""))
                    if reasoning_idx < len(reasoning_texts):
                        content = reasoning_texts[reasoning_idx]
                    else:
                        content = default_text
                    reasoning_idx += 1
                elif event_type == "brief_delta":
                    section = str(event.get("section", ""))
                    content = {
                        "section": section,
                        "text": self._brief_delta_text(demo_brief, section),
                    }
                elif event_type == "complete":
                    content = {
                        "question": question,
                        "brief": demo_brief,
                        "duration_ms": event.get("duration_ms", 0),
                        "query_class": query_class,
                        "session_context_used": follow_up_note is not None,
                    }
                elif event_type == "error":
                    content = event.get("message", "Unknown error")

                yield TraceStep(
                    step_index=step_index,
                    type=event_type,
                    tool_name=tool_name,
                    tool_args=tool_args,
                    content=content,
                    timestamp=timestamp,
                )

            except Exception as exc:
                logger.error(f"Error replaying demo trace step {idx}: {exc}")
                # Continue to next step rather than failing completely
                continue

    async def _run_live(
        self,
        question: str,
        session_context: dict[str, Any] | None = None,
    ) -> AsyncGenerator[TraceStep, None]:
        start = time.perf_counter()
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": build_system_prompt(self.tools.definitions),
            },
        ]

        follow_up_note = self._session_follow_up_note(session_context)
        if follow_up_note:
            key_sources = session_context.get("key_sources") if isinstance(session_context, dict) else []
            source_line = ", ".join(str(item) for item in key_sources[:4])
            messages.append(
                {
                    "role": "system",
                    "content": f"Session continuity note: {follow_up_note}. Prior key sources: {source_line or 'none'}.",
                }
            )

        messages.append({"role": "user", "content": question})
        tool_schema = self.tools.to_openai_tools()
        step_index = 0
        tool_calls = 0

        while tool_calls < self.max_tool_calls:
            try:
                response = await self.call_glm(messages=messages, tools=tool_schema, stream=False)
            except Exception as exc:
                yield TraceStep(
                    step_index=step_index,
                    type="error",
                    content=f"GLM call failed: {exc}",
                    timestamp=_iso_now(),
                )
                return

            payload = response.json()
            message = payload.get("choices", [{}])[0].get("message", {})
            content = str(message.get("content") or "")
            called_tools = message.get("tool_calls") or []

            if called_tools:
                for call in called_tools:
                    fn = call.get("function", {})
                    name = str(fn.get("name", ""))
                    args_raw = str(fn.get("arguments") or "{}")
                    try:
                        args = json.loads(args_raw)
                    except json.JSONDecodeError:
                        args = {}

                    yield TraceStep(
                        step_index=step_index,
                        type="tool_call",
                        tool_name=name,
                        tool_args=args,
                        content={"id": call.get("id")},
                        timestamp=_iso_now(),
                    )
                    step_index += 1

                    try:
                        result = await self.tools.execute(name, args)
                    except Exception as exc:
                        result = {"error": str(exc)}

                    yield TraceStep(
                        step_index=step_index,
                        type="tool_result",
                        tool_name=name,
                        tool_args=args,
                        content=result,
                        timestamp=_iso_now(),
                    )
                    step_index += 1
                    tool_calls += 1

                    messages.append({"role": "assistant", "content": "", "tool_calls": [call]})
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.get("id", ""),
                            "name": name,
                            "content": json.dumps(result),
                        }
                    )

                    self.tools_called.append(name)

                    # Self-reflection checkpoint at intervals
                    if (
                        self.enable_reflection
                        and tool_calls % self.reflection_interval == 0
                        and tool_calls < self.max_tool_calls
                    ):
                        yield TraceStep(
                            step_index=step_index,
                            type="reflection",
                            tool_name=name,
                            tool_args=args,
                            content={
                                "step": tool_calls,
                                "tools_used": self.tools_called.copy(),
                                "message": "Reflection checkpoint: evaluating if sufficient data gathered",
                            },
                            timestamp=_iso_now(),
                        )
                        step_index += 1

                    if tool_calls >= self.max_tool_calls:
                        break
                continue

            if content:
                yield TraceStep(
                    step_index=step_index,
                    type="reasoning",
                    content=content,
                    timestamp=_iso_now(),
                )
                step_index += 1

            candidate = _extract_json_payload(content)
            if candidate is None:
                continue

            candidate.setdefault("question", question)
            candidate.setdefault("created_at", _iso_now())
            candidate.setdefault("trace_steps", list(range(step_index + 1)))
            candidate.setdefault("query_class", self._classify_query(question))
            candidate.setdefault("methodology_summary", "Tool-driven synthesis with evidence cross-checking.")
            if follow_up_note:
                candidate.setdefault("follow_up_context", follow_up_note)

            try:
                brief = ResearchBrief.model_validate(candidate)
            except Exception as exc:
                yield TraceStep(
                    step_index=step_index,
                    type="error",
                    content=f"Brief validation failed: {exc}",
                    timestamp=_iso_now(),
                )
                return

            duration_ms = int((time.perf_counter() - start) * 1000)
            yield TraceStep(
                step_index=step_index,
                type="complete",
                content={
                    "brief": brief.model_dump(),
                    "duration_ms": duration_ms,
                    "query_class": brief.query_class or self._classify_query(question),
                    "session_context_used": follow_up_note is not None,
                },
                timestamp=_iso_now(),
            )
            return

        yield TraceStep(
            step_index=step_index,
            type="error",
            content="Tool call limit exceeded",
            timestamp=_iso_now(),
        )
