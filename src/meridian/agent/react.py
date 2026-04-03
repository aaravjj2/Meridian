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

from meridian.agent.prompt import build_reflection_prompt, build_system_prompt
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
        resolved_mode = (mode or ("demo" if self.demo_mode else "live")).strip().lower()
        if resolved_mode == "demo":
            async for step in self._run_demo(question):
                yield step
            return

        async for step in self._run_live(question):
            yield step

    async def _run_demo(self, question: str) -> AsyncGenerator[TraceStep, None]:
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
                    content = event.get("text", "")
                elif event_type == "brief_delta":
                    content = {
                        "section": event.get("section"),
                        "text": event.get("text", ""),
                    }
                elif event_type == "complete":
                    content = {
                        "question": question,
                        "brief": event.get("brief", {}),
                        "duration_ms": event.get("duration_ms", 0),
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

    async def _run_live(self, question: str) -> AsyncGenerator[TraceStep, None]:
        start = time.perf_counter()
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": build_system_prompt(self.tools.definitions),
            },
            {"role": "user", "content": question},
        ]
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
                content={"brief": brief.model_dump(), "duration_ms": duration_ms},
                timestamp=_iso_now(),
            )
            return

        yield TraceStep(
            step_index=step_index,
            type="error",
            content="Tool call limit exceeded",
            timestamp=_iso_now(),
        )
