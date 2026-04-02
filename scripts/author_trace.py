from __future__ import annotations

import json
import sys
from pathlib import Path

from meridian.normalisation.schemas import ResearchBrief


ROOT = Path(__file__).resolve().parents[1]
TRACE_PATH = ROOT / "data" / "fixtures" / "traces" / "demo_trace.json"
REQUIRED_TYPES = {"tool_call", "tool_result", "reasoning", "brief_delta", "complete"}
REQUIRED_BRIEF_SECTIONS = {"thesis", "bull_case", "bear_case", "key_risks"}


def main() -> int:
    if not TRACE_PATH.exists():
        print(f"Trace file not found: {TRACE_PATH}")
        return 1

    payload = json.loads(TRACE_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        print("Trace must be a JSON array of steps")
        return 1

    if len(payload) < 15:
        print("Trace must include at least 15 steps")
        return 1

    seen_types = {str(step.get("type", "")) for step in payload if isinstance(step, dict)}
    missing = REQUIRED_TYPES - seen_types
    if missing:
        print(f"Missing required step types: {sorted(missing)}")
        return 1

    if payload[-1].get("type") != "complete":
        print("Final step must be type=complete")
        return 1

    tool_call_count = 0
    reasoning_count = 0
    brief_sections: set[str] = set()

    for idx, step in enumerate(payload):
        if not isinstance(step, dict):
            print(f"Step {idx} must be an object")
            return 1

        step_type = str(step.get("type", ""))
        if step_type == "tool_call":
            tool_call_count += 1
            next_step = payload[idx + 1] if idx + 1 < len(payload) else None
            if not isinstance(next_step, dict) or next_step.get("type") != "tool_result":
                print(f"Step {idx} is tool_call but is not followed by tool_result")
                return 1

        if step_type == "reasoning":
            reasoning_count += 1

        if step_type == "brief_delta":
            section = str(step.get("section", "")).strip()
            if section:
                brief_sections.add(section)

    if tool_call_count < 5:
        print("Trace must include at least 5 tool calls")
        return 1

    if reasoning_count < 3:
        print("Trace must include at least 3 reasoning steps")
        return 1

    if not REQUIRED_BRIEF_SECTIONS.issubset(brief_sections):
        missing_sections = sorted(REQUIRED_BRIEF_SECTIONS - brief_sections)
        print(f"Missing brief_delta sections: {missing_sections}")
        return 1

    final_brief = payload[-1].get("brief")
    if not isinstance(final_brief, dict):
        print("Final complete step must contain brief object")
        return 1

    try:
        ResearchBrief.model_validate(final_brief)
    except Exception as exc:
        print(f"Final brief schema validation failed: {exc}")
        return 1

    print("demo_trace.json is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
