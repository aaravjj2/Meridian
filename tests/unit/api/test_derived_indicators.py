from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.routers import research as research_router
from meridian.normalisation.schemas import DerivedIndicator
from meridian.workspace import session_store as session_store_module


client = TestClient(app)


@pytest.fixture(autouse=True)
def _isolated_workspace_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    store_path = tmp_path / "research_sessions"
    monkeypatch.setenv("MERIDIAN_SESSION_STORE_DIR", str(store_path))
    session_store_module._STORE = None
    research_router.SESSION_CONTEXT.clear()
    yield
    session_store_module._STORE = None
    research_router.SESSION_CONTEXT.clear()


def _collect_events(question: str, session_id: str | None = None) -> list[dict]:
    events: list[dict] = []
    payload: dict[str, object] = {"question": question, "mode": "demo"}
    if session_id:
        payload["session_id"] = session_id

    with client.stream("POST", "/api/v1/research", json=payload) as response:
        assert response.status_code == 200
        for line in response.iter_lines():
            if not line or not line.startswith("data: "):
                continue
            events.append(json.loads(line[6:]))
    return events


def _save_payload(question: str, session_id: str, events: list[dict], brief: dict) -> dict:
    complete_event = [e for e in events if e.get("type") == "complete"][0]
    return {
        "question": question,
        "mode": "demo",
        "session_id": session_id,
        "template_id": brief.get("template_id"),
        "brief": complete_event.get("brief", brief),
        "trace_events": events,
        "evidence_state": None,
        "evaluation": complete_event.get("evaluation"),
    }


def test_derived_indicators_schema_validation():
    """Test that DerivedIndicator schema validates correctly"""
    indicator = DerivedIndicator(
        indicator_id="ind-test-123",
        title="Test Indicator",
        value=1.5,
        unit="%",
        display_hint="percentage change",
        computation_kind="rate_of_change",
        source_refs=["fred:test"],
        snapshot_id="snap-test123",
        snapshot_kind="fixture",
        computation_timestamp="2026-04-05T00:00:00Z",
        observed_at="2026-04-05T00:00:00Z",
        deterministic=True,
        reasoning="Test reasoning",
        deterministic_signature="test-sig-123",
    )

    assert indicator.indicator_id == "ind-test-123"
    assert indicator.value == 1.5
    assert indicator.computation_kind == "rate_of_change"
    assert indicator.source_refs == ["fred:test"]


def test_derived_indicators_in_research_response():
    """Test that derived indicators appear in research response"""
    question = "What is the current GDP growth trend?"
    session_id = "wave21-derived-indicators"

    events = _collect_events(question=question, session_id=session_id)
    complete = [e for e in events if e.get("type") == "complete"]

    assert len(complete) > 0, "Should have at least one complete event"

    brief = complete[0].get("brief")
    assert isinstance(brief, dict), "Brief should be a dict"

    derived_indicators = brief.get("derived_indicators")
    assert isinstance(derived_indicators, list), "Derived indicators should be a list"

    if len(derived_indicators) > 0:
        indicator = derived_indicators[0]
        assert "indicator_id" in indicator
        assert "title" in indicator
        assert "value" in indicator
        assert "computation_kind" in indicator
        assert "source_refs" in indicator
        assert "deterministic_signature" in indicator


def test_derived_indicators_persist_in_saved_session():
    """Test that derived indicators persist through save/load cycle"""
    question = "What are the inflation trends?"
    session_id = "wave21-persistence"

    events = _collect_events(question=question, session_id=session_id)
    complete = [e for e in events if e.get("type") == "complete"]

    assert len(complete) > 0

    brief = complete[0].get("brief")
    assert isinstance(brief, dict)

    saved_response = client.post(
        "/api/v1/research/sessions",
        json=_save_payload(question=question, session_id=session_id, events=events, brief=brief),
    )
    assert saved_response.status_code == 200
    saved_id = saved_response.json()["id"]

    get_response = client.get(f"/api/v1/research/sessions/{saved_id}")
    assert get_response.status_code == 200

    loaded_session = get_response.json()
    assert "brief" in loaded_session
    assert "derived_indicators" in loaded_session["brief"]

    original_indicators = brief.get("derived_indicators", [])
    loaded_indicators = loaded_session["brief"].get("derived_indicators", [])

    assert len(original_indicators) == len(loaded_indicators)


def test_derived_indicators_deterministic():
    """Test that derived indicators are deterministic for same inputs"""
    question = "Analyze unemployment rate trends"
    session_id_1 = "wave21-deterministic-1"
    session_id_2 = "wave21-deterministic-2"

    events_1 = _collect_events(question=question, session_id=session_id_1)
    complete_1 = [e for e in events_1 if e.get("type") == "complete"][0]
    brief_1 = complete_1.get("brief", {})
    indicators_1 = brief_1.get("derived_indicators", [])

    events_2 = _collect_events(question=question, session_id=session_id_2)
    complete_2 = [e for e in events_2 if e.get("type") == "complete"][0]
    brief_2 = complete_2.get("brief", {})
    indicators_2 = brief_2.get("derived_indicators", [])

    if len(indicators_1) > 0 and len(indicators_2) > 0:
        sigs_1 = {ind["deterministic_signature"] for ind in indicators_1}
        sigs_2 = {ind["deterministic_signature"] for ind in indicators_2}

        assert sigs_1 == sigs_2, "Deterministic signatures should match"


def test_derived_indicator_provenance_completeness():
    """Test that derived indicators preserve provenance information"""
    question = "What is the interest rate outlook?"
    session_id = "wave21-provenance"

    events = _collect_events(question=question, session_id=session_id)
    complete = [e for e in events if e.get("type") == "complete"][0]
    brief = complete.get("brief", {})
    indicators = brief.get("derived_indicators", [])

    for indicator in indicators:
        assert "source_refs" in indicator
        assert isinstance(indicator["source_refs"], list)
        assert len(indicator["source_refs"]) > 0, "Each indicator must reference at least one source"

        assert "computation_timestamp" in indicator
        assert "deterministic_signature" in indicator

        if indicator.get("snapshot_kind"):
            assert indicator["snapshot_kind"] in ["fixture", "cache", "live_capture", "derived", "unknown"]


def test_derived_indicator_kinds():
    """Test that all computation kinds are present and valid"""
    valid_kinds = {
        "rate_of_change",
        "spread",
        "delta",
        "trend_bucket",
        "aggregate_freshness",
        "conflict_pressure",
        "helper_summary",
        "volatility",
        "momentum",
        "correlation",
    }

    question = "Comprehensive market analysis"
    session_id = "wave21-kinds"

    events = _collect_events(question=question, session_id=session_id)
    complete = [e for e in events if e.get("type") == "complete"][0]
    brief = complete.get("brief", {})
    indicators = brief.get("derived_indicators", [])

    for indicator in indicators:
        computation_kind = indicator.get("computation_kind")
        assert computation_kind in valid_kinds, f"Invalid computation kind: {computation_kind}"


def test_volatility_indicators_computed():
    """Test that volatility indicators are computed correctly"""
    from apps.api.routers.research import _compute_volatility_indicators

    sources = [
        {
            "type": "fred",
            "id": "GDP",
            "preview": {
                "points": [
                    {"date": "2020-01-01", "value": 100.0},
                    {"date": "2020-04-01", "value": 95.0},
                    {"date": "2020-07-01", "value": 105.0},
                    {"date": "2020-10-01", "value": 110.0},
                ],
            },
        },
    ]

    indicators = _compute_volatility_indicators(sources, "demo", "2026-04-05T00:00:00Z")

    assert len(indicators) > 0
    assert indicators[0].computation_kind == "volatility"
    assert indicators[0].unit == "%"
    assert indicators[0].value > 0  # CV should be positive


def test_momentum_indicators_computed():
    """Test that momentum indicators are computed correctly"""
    from apps.api.routers.research import _compute_momentum_indicators

    sources = [
        {
            "type": "fred",
            "id": "UNRATE",
            "preview": {
                "points": [
                    {"date": "2020-01-01", "value": 3.5},
                    {"date": "2020-04-01", "value": 4.0},
                    {"date": "2020-07-01", "value": 5.0},
                    {"date": "2020-10-01", "value": 6.0},
                ],
            },
        },
    ]

    indicators = _compute_momentum_indicators(sources, "demo", "2026-04-05T00:00:00Z")

    assert len(indicators) > 0
    assert indicators[0].computation_kind == "momentum"
    assert indicators[0].unit == "%"
    # Momentum should be positive (growing from 3.5 to 6.0)
    assert indicators[0].value > 0


def test_correlation_indicators_computed():
    """Test that correlation indicators are computed correctly"""
    from apps.api.routers.research import _compute_correlation_indicators

    sources = [
        {
            "type": "fred",
            "id": "GDP",
            "preview": {
                "points": [
                    {"date": "2020-01-01", "value": 100.0},
                    {"date": "2020-04-01", "value": 102.0},
                    {"date": "2020-07-01", "value": 104.0},
                    {"date": "2020-10-01", "value": 106.0},
                ],
            },
        },
        {
            "type": "fred",
            "id": "GDPPOT",
            "preview": {
                "points": [
                    {"date": "2020-01-01", "value": 98.0},
                    {"date": "2020-04-01", "value": 100.0},
                    {"date": "2020-07-01", "value": 102.0},
                    {"date": "2020-10-01", "value": 104.0},
                ],
            },
        },
    ]

    indicators = _compute_correlation_indicators(sources, "demo", "2026-04-05T00:00:00Z")

    assert len(indicators) > 0
    assert indicators[0].computation_kind == "correlation"
    assert indicators[0].unit == "coef"
    # Correlation should be strongly positive for these series
    assert indicators[0].value > 0.5
