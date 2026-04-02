from __future__ import annotations

import pytest

from meridian.agent.react import ResearchAgent


@pytest.mark.asyncio
async def test_react_demo_trace_sequence() -> None:
    agent = ResearchAgent(demo_mode=True)
    steps = [step async for step in agent.run("demo question", mode="demo")]

    assert len(steps) >= 15
    assert steps[0].type == "tool_call"
    assert any(step.type == "reasoning" for step in steps)
    assert steps[-1].type == "complete"


class _FakeResponse:
    def json(self) -> dict:
        return {
            "choices": [
                {
                    "message": {
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "fred_fetch",
                                    "arguments": '{"series_id":"T10Y2Y"}',
                                },
                            }
                        ],
                    }
                }
            ]
        }


@pytest.mark.asyncio
async def test_react_hard_cap_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    agent = ResearchAgent(demo_mode=False, max_tool_calls=2)

    async def _fake_call_glm(messages, tools, stream=True):
        return _FakeResponse()

    monkeypatch.setattr(agent, "call_glm", _fake_call_glm)

    steps = [step async for step in agent.run("live question", mode="live")]
    tool_calls = [step for step in steps if step.type == "tool_call"]

    assert len(tool_calls) == 2
    assert steps[-1].type == "error"
