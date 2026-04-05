from __future__ import annotations

import asyncio
from collections import Counter
import copy
import hashlib
import json
import re
import uuid
from datetime import UTC, datetime
from typing import Any, AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from meridian.agent.react import ResearchAgent
from meridian.agent.templates import list_research_templates, resolve_research_template
from meridian.normalisation.schemas import (
    DerivedIndicator,
    DerivedIndicatorProvenance,
    ResearchBrief,
    ResearchTemplateDefinition,
    ResearchTemplateId,
    TraceStep,
)
from meridian.workspace.session_store import get_session_store


router = APIRouter(tags=["research"])


class ResearchRequest(BaseModel):
    question: str = Field(min_length=3)
    mode: str = "demo"
    session_id: str | None = Field(default=None, min_length=4, max_length=64)
    template_id: ResearchTemplateId | None = None


class ResearchTemplateListResponse(BaseModel):
    templates: list[ResearchTemplateDefinition]
    count: int


SESSION_CACHE_MAX = 64
SESSION_CONTEXT: dict[str, dict[str, Any]] = {}


@router.get("/research/templates")
async def list_templates() -> ResearchTemplateListResponse:
    templates = list_research_templates()
    return ResearchTemplateListResponse(templates=templates, count=len(templates))


def _iso_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _freshness_from_hours(hours: float | None) -> str:
    if hours is None:
        return "unknown"
    if hours <= 24 * 7:
        return "fresh"
    if hours <= 24 * 180:
        return "aging"
    return "stale"


def _source_tool_name(source_type: str) -> str:
    mapping = {
        "fred": "fred_fetch",
        "market": "prediction_market_fetch",
        "news": "news_fetch",
        "edgar": "edgar_fetch",
    }
    return mapping.get(source_type, "unknown")


def _derive_observed_at(source: dict[str, Any], captured_at: str) -> str:
    preview = source.get("preview")
    if isinstance(preview, dict):
        points = preview.get("points")
        if isinstance(points, list) and points:
            last_point = points[-1]
            if isinstance(last_point, dict):
                date_value = last_point.get("date")
                if isinstance(date_value, str) and date_value.strip():
                    if "T" in date_value:
                        return date_value
                    return f"{date_value}T00:00:00Z"

        for key in ["last_updated", "updated_at", "as_of", "timestamp", "scored_at", "filed_date"]:
            value = preview.get(key)
            if isinstance(value, str) and value.strip():
                if "T" in value:
                    return value
                return f"{value}T00:00:00Z"

    return captured_at


def _compute_freshness(observed_at: str, captured_at: str) -> tuple[str, float | None]:
    observed_dt = _parse_iso(observed_at)
    captured_dt = _parse_iso(captured_at)
    if observed_dt is None or captured_dt is None:
        return "unknown", None
    age_hours = max(0.0, (captured_dt - observed_dt).total_seconds() / 3600)
    return _freshness_from_hours(age_hours), round(age_hours, 2)


def _hash_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize_snapshot_kind(value: Any) -> str:
    candidate = str(value or "").strip().lower()
    if candidate in {"fixture", "cache", "live_capture", "derived", "unknown"}:
        return candidate
    return "unknown"


def _cache_lineage_from_snapshot_kind(snapshot_kind: str) -> str:
    if snapshot_kind == "fixture":
        return "fixture"
    if snapshot_kind == "cache":
        return "cache"
    if snapshot_kind == "live_capture":
        return "fresh_pull"
    if snapshot_kind == "derived":
        return "derived"
    return "unknown"


def _state_label_from_provenance(snapshot_kind: str, cache_lineage: str) -> str:
    if snapshot_kind == "fixture" or cache_lineage == "fixture":
        return "fixture"
    if snapshot_kind == "cache" or cache_lineage == "cache":
        return "cached"
    if snapshot_kind == "live_capture" or cache_lineage == "fresh_pull":
        return "live"
    if snapshot_kind == "derived" or cache_lineage == "derived":
        return "derived"
    return "unknown"


def _compute_rate_of_change_indicators(
    sources: list[dict[str, Any]],
    mode: str,
    captured_at: str,
) -> list[DerivedIndicator]:
    indicators = []

    for source in sources:
        if not isinstance(source, dict):
            continue

        source_type = source.get("type")
        source_id = source.get("id")
        source_ref = f"{source_type}:{source_id}"
        preview = source.get("preview")

        if not isinstance(preview, dict):
            continue

        points = preview.get("points")
        if not isinstance(points, list) or len(points) < 2:
            continue

        try:
            latest_point = points[-1]
            previous_point = points[-2]

            if not isinstance(latest_point, dict) or not isinstance(previous_point, dict):
                continue

            latest_value = float(latest_point.get("value", 0))
            previous_value = float(previous_point.get("value", 0))

            if previous_value == 0:
                continue

            rate_of_change = ((latest_value - previous_value) / abs(previous_value)) * 100

            indicator_id = f"ind-roc-{source_type}-{source_id}-{hashlib.sha256(source_ref.encode()).hexdigest()[:8]}"

            snapshot_kind = "unknown"
            snapshot_id = None
            provenance = source.get("provenance")
            if isinstance(provenance, dict):
                snapshot_info = provenance.get("snapshot")
                if isinstance(snapshot_info, dict):
                    snapshot_kind = snapshot_info.get("snapshot_kind", "unknown")
                    snapshot_id = snapshot_info.get("snapshot_id")

            reasoning = f"Rate of change computed from {previous_value:.2f} to {latest_value:.2f} over most recent period"
            if abs(rate_of_change) > 5:
                reasoning += " (significant movement)"
            elif abs(rate_of_change) > 1:
                reasoning += " (moderate movement)"

            indicator_signature_payload = {
                "indicator_id": indicator_id,
                "source_ref": source_ref,
                "rate_of_change": round(rate_of_change, 2),
                "computation_timestamp": captured_at,
            }
            deterministic_signature = hashlib.sha256(
                json.dumps(indicator_signature_payload, sort_keys=True).encode()
            ).hexdigest()

            indicator = DerivedIndicator(
                indicator_id=indicator_id,
                title=f"{source_type.upper()} Rate of Change",
                value=round(rate_of_change, 2),
                unit="%",
                display_hint="percentage_change_from_previous_period",
                computation_kind="rate_of_change",
                source_refs=[source_ref],
                snapshot_id=snapshot_id,
                snapshot_kind=snapshot_kind,
                computation_timestamp=captured_at,
                observed_at=latest_point.get("date"),
                deterministic=(mode == "demo" and snapshot_kind == "fixture") or (snapshot_kind == "fixture"),
                reasoning=reasoning,
                deterministic_signature=deterministic_signature,
            )
            indicators.append(indicator)
        except (ValueError, TypeError, KeyError):
            continue

    return indicators


def _compute_spread_indicators(
    brief: dict[str, Any],
    sources: list[dict[str, Any]],
    mode: str,
    captured_at: str,
) -> list[DerivedIndicator]:
    indicators = []

    bull_claims = brief.get("bull_case", [])
    bear_claims = brief.get("bear_case", [])

    if not isinstance(bull_claims, list) or not isinstance(bear_claims, list):
        return indicators

    bull_count = len(bull_claims)
    bear_count = len(bear_claims)
    total_claims = bull_count + bear_count

    if total_claims == 0:
        return indicators

    spread = abs(bull_count - bear_count)
    spread_ratio = spread / total_claims if total_claims > 0 else 0

    indicator_id = f"ind-spread-claims-{hashlib.sha256(captured_at.encode()).hexdigest()[:8]}"

    source_refs = {f"{s.get('type')}:{s.get('id')}" for s in sources if isinstance(s, dict)}

    reasoning = f"Claim spread: {bull_count} bull vs {bear_count} bear (spread of {spread})"
    if spread_ratio > 0.3:
        reasoning += " (strong imbalance)"
    elif spread_ratio > 0.1:
        reasoning += " (moderate imbalance)"

    indicator_signature_payload = {
        "indicator_id": indicator_id,
        "bull_count": bull_count,
        "bear_count": bear_count,
        "spread": spread,
        "computation_timestamp": captured_at,
    }
    deterministic_signature = hashlib.sha256(
        json.dumps(indicator_signature_payload, sort_keys=True).encode()
    ).hexdigest()

    indicator = DerivedIndicator(
        indicator_id=indicator_id,
        title="Claim Spread Indicator",
        value=spread_ratio,
        unit="ratio",
        display_hint="absolute_difference_normalized_by_total_claims",
        computation_kind="spread",
        source_refs=list(source_refs),
        snapshot_id=None,
        snapshot_kind="derived",
        computation_timestamp=captured_at,
        observed_at=None,
        deterministic=(mode == "demo"),
        reasoning=reasoning,
        deterministic_signature=deterministic_signature,
    )
    indicators.append(indicator)

    return indicators


def _compute_trend_bucket_indicators(
    sources: list[dict[str, Any]],
    mode: str,
    captured_at: str,
) -> list[DerivedIndicator]:
    indicators = []

    for source in sources:
        if not isinstance(source, dict):
            continue

        source_type = source.get("type")
        source_id = source.get("id")
        source_ref = f"{source_type}:{source_id}"
        preview = source.get("preview")

        if not isinstance(preview, dict):
            continue

        points = preview.get("points")
        if not isinstance(points, list) or len(points) < 3:
            continue

        try:
            values = []
            for point in points[-3:]:
                if isinstance(point, dict) and "value" in point:
                    values.append(float(point["value"]))

            if len(values) < 3:
                continue

            changes = [values[i] - values[i-1] for i in range(1, len(values))]

            if all(c > 0 for c in changes):
                trend = "increasing"
                trend_score = 1.0
            elif all(c < 0 for c in changes):
                trend = "decreasing"
                trend_score = -1.0
            elif abs(sum(changes)) < 0.01 * len(values):
                trend = "stable"
                trend_score = 0.0
            else:
                trend = "volatile"
                trend_score = 0.5

            indicator_id = f"ind-trend-{source_type}-{source_id}-{hashlib.sha256(source_ref.encode()).hexdigest()[:8]}"

            snapshot_kind = "unknown"
            snapshot_id = None
            provenance = source.get("provenance")
            if isinstance(provenance, dict):
                snapshot_info = provenance.get("snapshot")
                if isinstance(snapshot_info, dict):
                    snapshot_kind = snapshot_info.get("snapshot_kind", "unknown")
                    snapshot_id = snapshot_info.get("snapshot_id")

            reasoning = f"Time series trend over last {len(changes)} periods: {trend}"

            indicator_signature_payload = {
                "indicator_id": indicator_id,
                "source_ref": source_ref,
                "trend": trend,
                "trend_score": trend_score,
                "computation_timestamp": captured_at,
            }
            deterministic_signature = hashlib.sha256(
                json.dumps(indicator_signature_payload, sort_keys=True).encode()
            ).hexdigest()

            indicator = DerivedIndicator(
                indicator_id=indicator_id,
                title=f"{source_type.upper()} Trend Classification",
                value=trend_score,
                unit="score",
                display_hint=f"trend_classification: {trend}",
                computation_kind="trend_bucket",
                source_refs=[source_ref],
                snapshot_id=snapshot_id,
                snapshot_kind=snapshot_kind,
                computation_timestamp=captured_at,
                observed_at=points[-1].get("date") if isinstance(points[-1], dict) else None,
                deterministic=(mode == "demo" and snapshot_kind == "fixture") or (snapshot_kind == "fixture"),
                reasoning=reasoning,
                deterministic_signature=deterministic_signature,
            )
            indicators.append(indicator)
        except (ValueError, TypeError, KeyError):
            continue

    return indicators


def _compute_aggregate_freshness_indicator(
    sources: list[dict[str, Any]],
    mode: str,
    captured_at: str,
) -> list[DerivedIndicator]:
    indicators = []

    fresh_count = 0
    aging_count = 0
    stale_count = 0
    unknown_count = 0

    for source in sources:
        if not isinstance(source, dict):
            continue

        provenance = source.get("provenance")
        if isinstance(provenance, dict):
            freshness = provenance.get("freshness", "unknown")
            if freshness == "fresh":
                fresh_count += 1
            elif freshness == "aging":
                aging_count += 1
            elif freshness == "stale":
                stale_count += 1
            else:
                unknown_count += 1

    total_count = len(sources)
    if total_count == 0:
        return indicators

    fresh_ratio = fresh_count / total_count
    staleness_index = (fresh_count * 0 + aging_count * 1 + stale_count * 2) / total_count if total_count > 0 else 0

    indicator_id = f"ind-freshness-aggregate-{hashlib.sha256(captured_at.encode()).hexdigest()[:8]}"

    source_refs = [f"{s.get('type')}:{s.get('id')}" for s in sources if isinstance(s, dict)]

    reasoning = f"Aggregate freshness: {fresh_count} fresh, {aging_count} aging, {stale_count} stale out of {total_count} sources"
    if fresh_ratio >= 0.7:
        reasoning += " (good data freshness)"
    elif fresh_ratio >= 0.4:
        reasoning += " (moderate freshness)"
    else:
        reasoning += " (poor freshness - consider refreshing)"

    indicator_signature_payload = {
        "indicator_id": indicator_id,
        "fresh_count": fresh_count,
        "aging_count": aging_count,
        "stale_count": stale_count,
        "staleness_index": round(staleness_index, 2),
        "computation_timestamp": captured_at,
    }
    deterministic_signature = hashlib.sha256(
        json.dumps(indicator_signature_payload, sort_keys=True).encode()
    ).hexdigest()

    indicator = DerivedIndicator(
        indicator_id=indicator_id,
        title="Aggregate Data Freshness",
        value=staleness_index,
        unit="index",
        display_hint="0=fresh, 1=aging, 2=stale",
        computation_kind="aggregate_freshness",
        source_refs=source_refs,
        snapshot_id=None,
        snapshot_kind="derived",
        computation_timestamp=captured_at,
        observed_at=None,
        deterministic=(mode == "demo"),
        reasoning=reasoning,
        deterministic_signature=deterministic_signature,
    )
    indicators.append(indicator)

    return indicators


def _compute_derived_indicators(
    brief_payload: dict[str, Any],
    mode: str,
    trace_events: list[dict[str, Any]],
) -> list[DerivedIndicator]:
    sources = brief_payload.get("sources", [])
    if not isinstance(sources, list):
        sources = []
        brief_payload["sources"] = sources

    captured_at = str(brief_payload.get("created_at") or _iso_now())

    all_indicators = []

    all_indicators.extend(_compute_rate_of_change_indicators(sources, mode, captured_at))
    all_indicators.extend(_compute_spread_indicators(brief_payload, sources, mode, captured_at))
    all_indicators.extend(_compute_trend_bucket_indicators(sources, mode, captured_at))
    all_indicators.extend(_compute_aggregate_freshness_indicator(sources, mode, captured_at))

    return all_indicators


def _state_label_from_provenance(snapshot_kind: str, cache_lineage: str) -> str:
    if snapshot_kind == "fixture" or cache_lineage == "fixture":
        return "fixture"
    if snapshot_kind == "cache" or cache_lineage == "cache":
        return "cached"
    if snapshot_kind == "live_capture" or cache_lineage == "fresh_pull":
        return "live"
    if snapshot_kind == "derived" or cache_lineage == "derived":
        return "derived"
    return "unknown"


def _latest_iso_timestamp(values: list[str]) -> str | None:
    parsed = [_parse_iso(value) for value in values if value]
    parsed = [item for item in parsed if item is not None]
    if not parsed:
        return None
    return max(parsed).isoformat().replace("+00:00", "Z")


def _preview_timestamp(preview: dict[str, Any], keys: list[str]) -> str | None:
    for key in keys:
        raw = preview.get(key)
        if isinstance(raw, str) and raw.strip():
            if "T" in raw:
                return raw
            return f"{raw}T00:00:00Z"
    return None


def _snapshot_kind_for_source(
    source: dict[str, Any],
    mode: str,
    existing_snapshot: dict[str, Any],
) -> str:
    explicit = _normalize_snapshot_kind(existing_snapshot.get("snapshot_kind"))
    if explicit != "unknown":
        return explicit

    preview = source.get("preview") if isinstance(source.get("preview"), dict) else {}
    hinted = _normalize_snapshot_kind(preview.get("snapshot_kind") or preview.get("snapshot_source"))
    if hinted != "unknown":
        return hinted

    if mode == "demo":
        return "fixture"

    if any(key in preview for key in ["cached_at", "cache_timestamp", "cache_key", "cache_hit", "cache_snapshot_id"]):
        return "cache"
    if any(key in preview for key in ["derived_from", "computed_from", "calculation", "model_version"]):
        return "derived"

    if mode == "live":
        return "live_capture"
    return "unknown"


def _snapshot_dataset(source_type: str, source_id: str, preview: dict[str, Any]) -> str:
    if source_type == "fred":
        return f"fred:{str(preview.get('series_id') or source_id)}"
    if source_type == "market":
        platform = str(preview.get("platform") or "market")
        return f"{platform}:{source_id}"
    if source_type == "edgar":
        return f"edgar:{str(preview.get('cik') or source_id)}"
    if source_type == "news":
        return f"news:{str(preview.get('topic') or source_id)}"
    return f"{source_type}:{source_id}"


def _claim_ids_from_brief(brief: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for section, field in (("bull_case", "point"), ("bear_case", "point"), ("key_risks", "risk")):
        items = brief.get(section, [])
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            claim_id = item.get("claim_id")
            if isinstance(claim_id, str) and claim_id.strip() and field in item:
                ids.add(claim_id)
    return ids


def _attach_provenance_and_evaluation(
    brief_payload: dict[str, Any],
    mode: str,
    trace_events: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    brief = copy.deepcopy(brief_payload)
    captured_at = str(brief.get("created_at") or _iso_now())
    sources = brief.get("sources", [])
    freshness_counts: Counter[str] = Counter()
    snapshot_kind_counts: Counter[str] = Counter()
    cache_lineage_counts: Counter[str] = Counter()
    state_label_counts: Counter[str] = Counter()
    freshness_by_snapshot_kind: dict[str, Counter[str]] = {
        "fixture": Counter(),
        "cache": Counter(),
        "live_capture": Counter(),
        "derived": Counter(),
        "unknown": Counter(),
    }
    fetched_at_values: list[str] = []
    cached_at_values: list[str] = []
    generated_at_values: list[str] = []
    snapshot_checksum_coverage = 0

    if not isinstance(sources, list):
        sources = []
        brief["sources"] = sources

    for source in sources:
        if not isinstance(source, dict):
            continue
        source_type = str(source.get("type") or "")
        source_id = str(source.get("id") or "")
        source_ref = f"{source_type}:{source_id}"
        preview = source.get("preview") if isinstance(source.get("preview"), dict) else {}
        existing = source.get("provenance") if isinstance(source.get("provenance"), dict) else {}
        existing_snapshot = existing.get("snapshot") if isinstance(existing.get("snapshot"), dict) else {}
        observed_at = str(existing.get("observed_at") or _derive_observed_at(source, captured_at))
        freshness, freshness_hours = _compute_freshness(observed_at=observed_at, captured_at=captured_at)
        freshness_value = str(existing.get("freshness") or freshness)
        if freshness_value not in {"fresh", "aging", "stale", "unknown"}:
            freshness_value = freshness
        source_mode = str(existing.get("mode") or mode)
        if source_mode not in {"demo", "live"}:
            source_mode = "demo" if mode == "demo" else "live"

        snapshot_kind = _snapshot_kind_for_source(
            source=source,
            mode=source_mode,
            existing_snapshot=existing_snapshot,
        )
        cache_lineage = str(existing.get("cache_lineage") or _cache_lineage_from_snapshot_kind(snapshot_kind))
        if cache_lineage not in {"fixture", "cache", "fresh_pull", "derived", "unknown"}:
            cache_lineage = _cache_lineage_from_snapshot_kind(snapshot_kind)
        state_label = _state_label_from_provenance(snapshot_kind=snapshot_kind, cache_lineage=cache_lineage)

        dataset = str(existing_snapshot.get("dataset") or _snapshot_dataset(source_type, source_id, preview))
        dataset_version = existing_snapshot.get("dataset_version") or preview.get("dataset_version")
        if source_mode == "demo" and not dataset_version:
            dataset_version = "demo-fixture-v1"

        generated_at = (
            existing_snapshot.get("generated_at")
            or _preview_timestamp(preview, ["generated_at", "snapshot_generated_at", "as_of", "last_updated", "updated_at", "filed_date"])
        )
        cached_at = existing_snapshot.get("cached_at") or _preview_timestamp(
            preview, ["cached_at", "cache_timestamp", "cache_as_of"]
        )
        fetched_at = existing_snapshot.get("fetched_at") or _preview_timestamp(
            preview, ["fetched_at", "retrieved_at"]
        )

        if snapshot_kind == "fixture":
            generated_at = generated_at or observed_at
        elif snapshot_kind == "cache":
            cached_at = cached_at or observed_at
        elif snapshot_kind == "live_capture":
            fetched_at = fetched_at or captured_at
        elif snapshot_kind == "derived":
            generated_at = generated_at or captured_at

        if isinstance(fetched_at, str) and fetched_at.strip():
            fetched_at_values.append(fetched_at)
        if isinstance(cached_at, str) and cached_at.strip():
            cached_at_values.append(cached_at)
        if isinstance(generated_at, str) and generated_at.strip():
            generated_at_values.append(generated_at)

        snapshot_signature_payload = {
            "source_ref": source_ref,
            "snapshot_kind": snapshot_kind,
            "dataset": dataset,
            "dataset_version": dataset_version,
            "generated_at": generated_at,
            "cached_at": cached_at,
            "fetched_at": fetched_at,
            "preview_kind": preview.get("kind"),
            "mode": source_mode,
        }
        checksum_sha256 = str(existing_snapshot.get("checksum_sha256") or _hash_payload(snapshot_signature_payload))
        snapshot_id = str(existing_snapshot.get("snapshot_id") or f"snap-{checksum_sha256[:12]}")
        deterministic_snapshot = bool(existing_snapshot.get("deterministic", source_mode == "demo"))

        source["provenance"] = {
            "source_ref": source_ref,
            "tool_name": str(existing.get("tool_name") or _source_tool_name(source_type)),
            "mode": source_mode,
            "state_label": state_label,
            "cache_lineage": cache_lineage,
            "observed_at": observed_at,
            "captured_at": str(existing.get("captured_at") or captured_at),
            "freshness": freshness_value,
            "freshness_hours": existing.get("freshness_hours", freshness_hours),
            "deterministic": bool(existing.get("deterministic", mode == "demo")),
            "snapshot": {
                "snapshot_id": snapshot_id,
                "snapshot_kind": snapshot_kind,
                "dataset": dataset,
                "dataset_version": dataset_version,
                "generated_at": generated_at,
                "cached_at": cached_at,
                "fetched_at": fetched_at,
                "checksum_sha256": checksum_sha256,
                "deterministic": deterministic_snapshot,
            },
        }
        freshness_counts[source["provenance"]["freshness"]] += 1
        snapshot_kind_counts[snapshot_kind] += 1
        cache_lineage_counts[cache_lineage] += 1
        state_label_counts[state_label] += 1
        freshness_by_snapshot_kind[snapshot_kind][source["provenance"]["freshness"]] += 1
        if checksum_sha256:
            snapshot_checksum_coverage += 1

    brief["provenance_summary"] = {
        "captured_at": captured_at,
        "mode": mode,
        "deterministic": mode == "demo",
        "source_count": len(sources),
        "state_label_counts": {
            "fixture": state_label_counts.get("fixture", 0),
            "cached": state_label_counts.get("cached", 0),
            "live": state_label_counts.get("live", 0),
            "derived": state_label_counts.get("derived", 0),
            "unknown": state_label_counts.get("unknown", 0),
        },
        "freshness_counts": {
            "fresh": freshness_counts.get("fresh", 0),
            "aging": freshness_counts.get("aging", 0),
            "stale": freshness_counts.get("stale", 0),
            "unknown": freshness_counts.get("unknown", 0),
        },
    }

    brief["snapshot_summary"] = {
        "captured_at": captured_at,
        "mode": mode,
        "deterministic": mode == "demo",
        "snapshot_count": len(sources),
        "state_label_counts": {
            "fixture": state_label_counts.get("fixture", 0),
            "cached": state_label_counts.get("cached", 0),
            "live": state_label_counts.get("live", 0),
            "derived": state_label_counts.get("derived", 0),
            "unknown": state_label_counts.get("unknown", 0),
        },
        "snapshot_kind_counts": {
            "fixture": snapshot_kind_counts.get("fixture", 0),
            "cache": snapshot_kind_counts.get("cache", 0),
            "live_capture": snapshot_kind_counts.get("live_capture", 0),
            "derived": snapshot_kind_counts.get("derived", 0),
            "unknown": snapshot_kind_counts.get("unknown", 0),
        },
        "cache_lineage_counts": {
            "fixture": cache_lineage_counts.get("fixture", 0),
            "cache": cache_lineage_counts.get("cache", 0),
            "fresh_pull": cache_lineage_counts.get("fresh_pull", 0),
            "derived": cache_lineage_counts.get("derived", 0),
            "unknown": cache_lineage_counts.get("unknown", 0),
        },
        "freshness_by_snapshot_kind": {
            kind: {
                "fresh": counters.get("fresh", 0),
                "aging": counters.get("aging", 0),
                "stale": counters.get("stale", 0),
                "unknown": counters.get("unknown", 0),
            }
            for kind, counters in freshness_by_snapshot_kind.items()
        },
        "timing_summary": {
            "latest_fetched_at": _latest_iso_timestamp(fetched_at_values),
            "latest_cached_at": _latest_iso_timestamp(cached_at_values),
            "latest_generated_at": _latest_iso_timestamp(generated_at_values),
        },
        "snapshot_checksum_coverage": snapshot_checksum_coverage,
    }

    claim_ids = _claim_ids_from_brief(brief)
    source_claim_refs = {
        claim_ref
        for source in sources
        if isinstance(source, dict)
        for claim_ref in (source.get("claim_refs") or [])
        if isinstance(claim_ref, str)
    }
    trace_steps = [int(event.get("step", 0)) for event in trace_events]
    trace_step_order_valid = all(previous <= current for previous, current in zip(trace_steps, trace_steps[1:]))
    trace_step_unique = len(trace_steps) == len(set(trace_steps))
    unknown_count = freshness_counts.get("unknown", 0)
    deterministic_sources = sum(
        1
        for source in sources
        if isinstance(source, dict)
        and isinstance(source.get("provenance"), dict)
        and bool(source["provenance"].get("deterministic"))
    )
    snapshot_records = [
        source.get("provenance", {}).get("snapshot")
        for source in sources
        if isinstance(source, dict) and isinstance(source.get("provenance"), dict)
    ]
    snapshot_metadata_complete = all(
        isinstance(snapshot, dict)
        and str(snapshot.get("snapshot_id") or "").strip()
        and str(snapshot.get("dataset") or "").strip()
        and _normalize_snapshot_kind(snapshot.get("snapshot_kind")) != "unknown"
        for snapshot in snapshot_records
    )
    snapshot_source_consistency = all(
        isinstance(source, dict)
        and isinstance(source.get("provenance"), dict)
        and isinstance(source["provenance"].get("snapshot"), dict)
        and (
            source["provenance"].get("mode") != "demo"
            or source["provenance"]["snapshot"].get("snapshot_kind") in {"fixture", "derived"}
        )
        for source in sources
    )
    cache_lineage_visibility = sum(cache_lineage_counts.values()) == len(sources)
    bundle_snapshot_ready = snapshot_checksum_coverage == len(sources) and snapshot_metadata_complete
    freshness_policy_rules: dict[str, dict[str, float]] = {
        "fred": {"max_age_hours": float(24 * 180), "warn_age_hours": float(24 * 30)},
        "market": {"max_age_hours": float(24 * 3), "warn_age_hours": float(24)},
        "news": {"max_age_hours": float(24 * 2), "warn_age_hours": float(12)},
        "edgar": {"max_age_hours": float(24 * 45), "warn_age_hours": float(24 * 15)},
    }
    freshness_policy_default = {"max_age_hours": float(24 * 30), "warn_age_hours": float(24 * 7)}
    freshness_policy_violations: list[dict[str, Any]] = []
    freshness_policy_warning_count = 0
    for source in sources:
        if not isinstance(source, dict):
            continue
        source_type = str(source.get("type") or "unknown")
        source_ref = f"{source_type}:{source.get('id')}"
        provenance = source.get("provenance") if isinstance(source.get("provenance"), dict) else {}
        freshness = str(provenance.get("freshness") or "unknown")
        freshness_hours = provenance.get("freshness_hours")
        hours_value = float(freshness_hours) if isinstance(freshness_hours, (int, float)) else None
        policy = freshness_policy_rules.get(source_type, freshness_policy_default)
        violation = (
            freshness == "unknown"
            or freshness == "stale"
            or (hours_value is not None and hours_value > float(policy["max_age_hours"]))
        )
        warning = (
            not violation
            and hours_value is not None
            and hours_value > float(policy["warn_age_hours"])
        )
        if warning:
            freshness_policy_warning_count += 1
        if violation:
            freshness_policy_violations.append(
                {
                    "source_ref": source_ref,
                    "source_type": source_type,
                    "freshness": freshness,
                    "freshness_hours": hours_value,
                    "max_age_hours": float(policy["max_age_hours"]),
                }
            )
    freshness_policy_passed = len(freshness_policy_violations) == 0

    checks = [
        {
            "check_id": "claim_source_coverage",
            "passed": claim_ids.issubset(source_claim_refs),
            "detail": "Every claim_id is linked by at least one source claim_ref.",
            "value": f"{len(source_claim_refs)}/{len(claim_ids)}",
        },
        {
            "check_id": "provenance_attached",
            "passed": all(
                isinstance(source, dict) and isinstance(source.get("provenance"), dict)
                for source in sources
            ),
            "detail": "Every source includes provenance metadata.",
            "value": len(sources),
        },
        {
            "check_id": "trace_step_order",
            "passed": trace_step_order_valid and trace_step_unique,
            "detail": "Trace steps are monotonic and unique.",
            "value": len(trace_steps),
        },
        {
            "check_id": "freshness_visibility",
            "passed": unknown_count == 0,
            "detail": "Every source has a resolved freshness state.",
            "value": len(sources) - unknown_count,
        },
        {
            "check_id": "freshness_policy_compliance",
            "passed": freshness_policy_passed,
            "detail": "Source freshness is within policy thresholds by source type.",
            "value": len(freshness_policy_violations),
        },
        {
            "check_id": "deterministic_mode_alignment",
            "passed": (mode != "demo") or (deterministic_sources == len(sources)),
            "detail": "Demo mode sources should all be deterministic.",
            "value": deterministic_sources,
        },
        {
            "check_id": "snapshot_metadata_complete",
            "passed": snapshot_metadata_complete,
            "detail": "Every source includes snapshot id, kind, and dataset metadata.",
            "value": len(snapshot_records),
        },
        {
            "check_id": "snapshot_source_consistency",
            "passed": snapshot_source_consistency,
            "detail": "Snapshot labels are consistent with source mode and lineage semantics.",
            "value": len(sources),
        },
        {
            "check_id": "cache_lineage_visibility",
            "passed": cache_lineage_visibility,
            "detail": "Snapshot summary exposes cache lineage coverage for all sources.",
            "value": sum(cache_lineage_counts.values()),
        },
        {
            "check_id": "bundle_snapshot_provenance_ready",
            "passed": bundle_snapshot_ready,
            "detail": "Snapshot checksum coverage is complete for offline bundle auditing.",
            "value": snapshot_checksum_coverage,
        },
    ]

    signature_payload = {
        "mode": mode,
        "query_class": brief.get("query_class"),
        "claim_ids": sorted(claim_ids),
        "source_refs": sorted(
            [
                f"{source.get('type')}:{source.get('id')}"
                for source in sources
                if isinstance(source, dict)
            ]
        ),
        "source_freshness": {
            f"{source.get('type')}:{source.get('id')}": (
                source.get("provenance", {}).get("freshness")
                if isinstance(source, dict)
                else "unknown"
            )
            for source in sources
            if isinstance(source, dict)
        },
        "source_snapshot_kind": {
            f"{source.get('type')}:{source.get('id')}": (
                source.get("provenance", {}).get("snapshot", {}).get("snapshot_kind")
                if isinstance(source, dict)
                else "unknown"
            )
            for source in sources
            if isinstance(source, dict)
        },
        "source_cache_lineage": {
            f"{source.get('type')}:{source.get('id')}": (
                source.get("provenance", {}).get("cache_lineage")
                if isinstance(source, dict)
                else "unknown"
            )
            for source in sources
            if isinstance(source, dict)
        },
        "source_state_label": {
            f"{source.get('type')}:{source.get('id')}": (
                source.get("provenance", {}).get("state_label")
                if isinstance(source, dict)
                else "unknown"
            )
            for source in sources
            if isinstance(source, dict)
        },
        "freshness_policy": {
            "version": "wave10-v1",
            "violation_count": len(freshness_policy_violations),
            "warning_count": freshness_policy_warning_count,
            "violations": [
                {
                    "source_ref": item["source_ref"],
                    "freshness": item["freshness"],
                }
                for item in freshness_policy_violations
            ],
        },
        "snapshot_summary": brief.get("snapshot_summary"),
        "trace_steps": trace_steps,
        "trace_types": [str(event.get("type", "")) for event in trace_events],
    }

    evaluation = {
        "version": "phase-7",
        "deterministic_signature": _hash_payload(signature_payload),
        "passed": all(bool(check.get("passed")) for check in checks),
        "checks": checks,
        "metrics": {
            "claim_count": len(claim_ids),
            "source_count": len(sources),
            "trace_event_count": len(trace_events),
            "stale_source_count": freshness_counts.get("stale", 0),
            "unknown_source_count": unknown_count,
            "freshness_policy_version": "wave10-v1",
            "freshness_policy_violation_count": len(freshness_policy_violations),
            "freshness_policy_warning_count": freshness_policy_warning_count,
            "freshness_policy_violations": [
                f"{item['source_ref']} ({item['freshness']})"
                for item in freshness_policy_violations
            ],
            "deterministic_source_count": deterministic_sources,
            "snapshot_count": len(snapshot_records),
            "fixture_snapshot_count": snapshot_kind_counts.get("fixture", 0),
            "cache_snapshot_count": snapshot_kind_counts.get("cache", 0),
            "live_capture_snapshot_count": snapshot_kind_counts.get("live_capture", 0),
            "derived_snapshot_count": snapshot_kind_counts.get("derived", 0),
            "unknown_snapshot_count": snapshot_kind_counts.get("unknown", 0),
            "fixture_state_count": state_label_counts.get("fixture", 0),
            "cached_state_count": state_label_counts.get("cached", 0),
            "live_state_count": state_label_counts.get("live", 0),
            "derived_state_count": state_label_counts.get("derived", 0),
            "unknown_state_count": state_label_counts.get("unknown", 0),
            "snapshot_checksum_coverage": snapshot_checksum_coverage,
        },
    }

    return brief, evaluation


def _compact_preview(payload: Any) -> list[list[Any]]:
    if isinstance(payload, dict) and "preview" in payload:
        payload = payload["preview"]
    if isinstance(payload, list):
        preview: list[list[Any]] = []
        for row in payload[:3]:
            if isinstance(row, dict):
                preview.append(list(row.values())[:2])
            elif isinstance(row, list):
                preview.append(row[:2])
            else:
                preview.append([row])
        return preview
    return []


def _resolve_session_id(value: str | None) -> str:
    if not value:
        return f"sess-{uuid.uuid4().hex[:12]}"
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-")
    if len(cleaned) < 4:
        return f"sess-{uuid.uuid4().hex[:12]}"
    return cleaned[:64]


def _update_session_context(session_id: str, brief_payload: dict[str, Any], question: str) -> None:
    sources = brief_payload.get("sources", [])
    key_sources = []
    for source in sources[:4]:
        source_type = source.get("type")
        source_id = source.get("id")
        if source_type and source_id:
            key_sources.append(f"{source_type}:{source_id}")

    SESSION_CONTEXT[session_id] = {
        "last_question": question,
        "last_thesis": brief_payload.get("thesis", ""),
        "last_query_class": brief_payload.get("query_class"),
        "last_template_id": brief_payload.get("template_id"),
        "last_template_title": brief_payload.get("template_title"),
        "key_sources": key_sources,
        "updated_at": _iso_now(),
    }

    # Keep cache bounded to avoid unbounded in-memory growth.
    if len(SESSION_CONTEXT) > SESSION_CACHE_MAX:
        oldest_id = next(iter(SESSION_CONTEXT))
        if oldest_id != session_id:
            SESSION_CONTEXT.pop(oldest_id, None)


def _restore_context_from_saved_session(session_id: str) -> dict[str, Any] | None:
    store = get_session_store()
    saved = store.get_latest_for_session(session_id)
    if saved is None:
        return None

    key_sources = [f"{source.type}:{source.id}" for source in saved.brief.sources[:4]]
    return {
        "last_question": saved.question,
        "last_thesis": saved.brief.thesis,
        "last_query_class": saved.brief.query_class,
        "last_template_id": saved.template_id,
        "last_template_title": saved.template_title,
        "key_sources": key_sources,
        "updated_at": _iso_now(),
        "restored_from_saved_session": saved.id,
    }


def _trace_to_event(step: TraceStep) -> dict[str, Any]:
    event = {
        "type": step.type,
        "step": step.step_index,
        "ts": step.timestamp,
    }

    if step.type == "tool_call":
        event.update(
            {
                "tool": step.tool_name,
                "args": step.tool_args or {},
            }
        )
    elif step.type == "tool_result":
        event.update(
            {
                "tool": step.tool_name,
                "preview": _compact_preview(step.content),
            }
        )
    elif step.type == "reasoning":
        event.update({"text": str(step.content or "")})
    elif step.type == "brief_delta":
        content = step.content if isinstance(step.content, dict) else {}
        event.update(
            {
                "section": content.get("section", "unknown"),
                "text": content.get("text", ""),
            }
        )
    elif step.type == "complete":
        content = step.content if isinstance(step.content, dict) else {}
        brief = content.get("brief", content)
        event.update(
            {
                "brief": brief,
                "duration_ms": int(content.get("duration_ms", 0)),
                "query_class": content.get("query_class"),
                "session_context_used": bool(content.get("session_context_used", False)),
            }
        )
    elif step.type == "error":
        event.update({"message": str(step.content or "Unknown error")})

    return event


@router.post("/research")
async def post_research(request: ResearchRequest) -> StreamingResponse:
    async def stream_events() -> AsyncGenerator[str, None]:
        session_id = _resolve_session_id(request.session_id)
        run_mode = request.mode.strip().lower()
        selected_template = resolve_research_template(request.template_id, request.question)
        prior_context = SESSION_CONTEXT.get(session_id)
        if prior_context is None and request.session_id:
            restored_context = _restore_context_from_saved_session(session_id)
            if restored_context is not None:
                prior_context = restored_context
                SESSION_CONTEXT[session_id] = restored_context

        agent = ResearchAgent(demo_mode=run_mode == "demo")
        complete_emitted = False
        last_step = -1
        emitted_events: list[dict[str, Any]] = []

        try:
            async with asyncio.timeout(120):
                async for trace_step in agent.run_with_context(
                    question=request.question,
                    mode=run_mode,
                    session_context=prior_context,
                    template_id=selected_template.id,
                ):
                    last_step = max(last_step, trace_step.step_index)
                    event = _trace_to_event(trace_step)
                    event["session_id"] = session_id
                    event["followup"] = prior_context is not None
                    event["template_id"] = selected_template.id
                    if event["type"] == "complete":
                        complete_emitted = True
                        brief_payload = event.get("brief")
                        if isinstance(brief_payload, dict):
                            brief_payload.setdefault("template_id", selected_template.id)
                            brief_payload.setdefault("template_title", selected_template.title)
                            brief_payload.setdefault("query_class", selected_template.query_class_default)
                            enriched_brief, evaluation = _attach_provenance_and_evaluation(
                                brief_payload=brief_payload,
                                mode=run_mode,
                                trace_events=[*emitted_events, event],
                            )

                            derived_indicators = _compute_derived_indicators(
                                brief_payload=enriched_brief,
                                mode=run_mode,
                                trace_events=[*emitted_events, event],
                            )
                            enriched_brief["derived_indicators"] = [ind.model_dump() for ind in derived_indicators]

                            event["brief"] = enriched_brief
                            event["evaluation"] = evaluation
                            event["provenance"] = enriched_brief.get("provenance_summary")
                            event["snapshot"] = enriched_brief.get("snapshot_summary")
                            event["template_id"] = enriched_brief.get("template_id")
                            _update_session_context(
                                session_id=session_id,
                                brief_payload=enriched_brief,
                                question=request.question,
                            )
                    emitted_events.append(event)
                    yield f"data: {json.dumps(event)}\n\n"
        except TimeoutError:
            error_step = last_step + 1
            timeout_event = {
                "type": "error",
                "step": error_step,
                "message": "research stream exceeded 120s timeout",
                "ts": _iso_now(),
                "session_id": session_id,
                "followup": prior_context is not None,
                "template_id": selected_template.id,
            }
            emitted_events.append(timeout_event)
            yield f"data: {json.dumps(timeout_event)}\n\n"
            last_step = error_step
        except Exception as exc:  # pragma: no cover - defensive runtime path
            error_step = last_step + 1
            error_event = {
                "type": "error",
                "step": error_step,
                "message": str(exc),
                "ts": _iso_now(),
                "session_id": session_id,
                "followup": prior_context is not None,
                "template_id": selected_template.id,
            }
            emitted_events.append(error_event)
            yield f"data: {json.dumps(error_event)}\n\n"
            last_step = error_step

        if not complete_emitted:
            completion = {
                "type": "complete",
                "step": last_step + 1,
                "brief": ResearchBrief(
                    question=request.question,
                    query_class=selected_template.query_class_default,
                    template_id=selected_template.id,
                    template_title=selected_template.title,
                    follow_up_context=(
                        f"Follow-up to prior question: {prior_context.get('last_question')}"
                        if prior_context and prior_context.get("last_question")
                        else None
                    ),
                    thesis="Research stream terminated with an error state.",
                    bull_case=[
                        {
                            "claim_id": "bull-1-fallback-contract-preserved",
                            "point": "Data retrieval completed for at least one source.",
                            "source_ref": "system:error",
                        },
                        {
                            "claim_id": "bull-2-fallback-complete-emitted",
                            "point": "Termination safeguards emitted completion event.",
                            "source_ref": "system:error",
                        },
                        {
                            "claim_id": "bull-3-fallback-client-recoverable",
                            "point": "Client can safely reset state.",
                            "source_ref": "system:error",
                        },
                    ],
                    bear_case=[
                        {
                            "claim_id": "bear-1-fallback-brief-incomplete",
                            "point": "Agent did not produce a full evidence-backed brief.",
                            "source_ref": "system:error",
                        },
                        {
                            "claim_id": "bear-2-fallback-retry-required",
                            "point": "Manual retry is required for complete analysis.",
                            "source_ref": "system:error",
                        },
                    ],
                    key_risks=[
                        {
                            "claim_id": "risk-1-fallback-runtime-failure",
                            "risk": "Execution path timed out or raised an exception.",
                            "source_ref": "system:error",
                        },
                        {
                            "claim_id": "risk-2-fallback-degraded-ux",
                            "risk": "Downstream UI must display degraded completion.",
                            "source_ref": "system:error",
                        },
                    ],
                    confidence=1,
                    confidence_rationale="Fallback completion after runtime error.",
                    sources=[
                        {
                            "type": "news",
                            "id": "system:error",
                            "excerpt": "Fallback completion to satisfy SSE contract.",
                            "claim_refs": [
                                "bull-1-fallback-contract-preserved",
                                "bull-2-fallback-complete-emitted",
                                "bull-3-fallback-client-recoverable",
                                "bear-1-fallback-brief-incomplete",
                                "bear-2-fallback-retry-required",
                                "risk-1-fallback-runtime-failure",
                                "risk-2-fallback-degraded-ux",
                            ],
                        }
                    ],
                    signal_conflicts=[
                        {
                            "conflict_id": "conflict-fallback-partial-success",
                            "title": "Contract Safety Versus Analysis Completeness",
                            "summary": "The stream remains structurally safe for clients, but the analytical content is incomplete and should be retried.",
                            "severity": "high",
                            "claim_refs": [
                                "bull-2-fallback-complete-emitted",
                                "bear-1-fallback-brief-incomplete",
                                "risk-1-fallback-runtime-failure",
                            ],
                            "source_refs": ["news:system:error"],
                        }
                    ],
                    created_at=_iso_now(),
                    trace_steps=[],
                ).model_dump(),
                "duration_ms": 0,
                "ts": _iso_now(),
                "session_context_used": prior_context is not None,
                "session_id": session_id,
                "followup": prior_context is not None,
                "template_id": selected_template.id,
            }
            if isinstance(completion.get("brief"), dict):
                enriched_brief, evaluation = _attach_provenance_and_evaluation(
                    brief_payload=completion["brief"],
                    mode=run_mode,
                    trace_events=[*emitted_events, completion],
                )

                derived_indicators = _compute_derived_indicators(
                    brief_payload=enriched_brief,
                    mode=run_mode,
                    trace_events=[*emitted_events, completion],
                )
                enriched_brief["derived_indicators"] = [ind.model_dump() for ind in derived_indicators]

                completion["brief"] = enriched_brief
                completion["evaluation"] = evaluation
                completion["provenance"] = enriched_brief.get("provenance_summary")
                completion["snapshot"] = enriched_brief.get("snapshot_summary")
                _update_session_context(
                    session_id=session_id,
                    brief_payload=enriched_brief,
                    question=request.question,
                )
            yield f"data: {json.dumps(completion)}\n\n"

    return StreamingResponse(stream_events(), media_type="text/event-stream")
