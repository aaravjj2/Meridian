from __future__ import annotations

import pytest

from meridian.agent.tools import ToolExecutor


@pytest.mark.asyncio
async def test_tool_executor_fred_fetch() -> None:
    tools = ToolExecutor(demo_mode=True)
    payload = await tools.execute("fred_fetch", {"series_id": "T10Y2Y"})
    assert payload["series_id"] == "T10Y2Y"
    assert len(payload["observations"]) >= 3


@pytest.mark.asyncio
async def test_tool_executor_prediction_market_fetch() -> None:
    tools = ToolExecutor(demo_mode=True)
    payload = await tools.execute(
        "prediction_market_fetch",
        {"platform": "kalshi", "event_slug": "fedcut"},
    )
    assert payload["platform"] == "kalshi"
    assert payload["ticker"].startswith("KX")


@pytest.mark.asyncio
async def test_tool_executor_vector_search() -> None:
    tools = ToolExecutor(demo_mode=True)
    payload = await tools.execute("vector_search", {"query": "yield curve", "top_k": 2})
    assert len(payload["results"]) == 2
    assert payload["results"][0]["score"] >= payload["results"][1]["score"]


@pytest.mark.asyncio
async def test_tool_executor_compute_feature() -> None:
    tools = ToolExecutor(demo_mode=True)
    payload = await tools.execute(
        "compute_feature",
        {"series_id": "FEDFUNDS", "feature_name": "monetary_regime"},
    )
    assert "regime" in payload


@pytest.mark.asyncio
async def test_tool_executor_unknown_tool() -> None:
    tools = ToolExecutor(demo_mode=True)
    with pytest.raises(KeyError):
        await tools.execute("not_a_tool", {})
