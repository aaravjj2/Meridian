from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import hashlib
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HARNESS_ROOT = ROOT / "artifacts" / "harness"


@dataclass
class LayerResult:
    layer: str
    command: str
    exit_code: int
    duration_ms: int
    passed: int | None = None
    failed: int = 0
    skipped: int = 0
    retries: int = 0
    log_path: str = ""
    details: dict[str, Any] = field(default_factory=dict)


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")


def _run_command(
    command: list[str],
    log_path: Path,
    env_overrides: dict[str, str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], int]:
    started = time.perf_counter()
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    proc = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    duration_ms = int((time.perf_counter() - started) * 1000)

    lines = [
        f"$ {' '.join(command)}",
        "",
        "--- STDOUT ---",
        proc.stdout,
        "",
        "--- STDERR ---",
        proc.stderr,
        "",
        f"exit_code={proc.returncode}",
        f"duration_ms={duration_ms}",
    ]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("\n".join(lines), encoding="utf-8")
    return proc, duration_ms


def _parse_vitest_json(report_path: Path) -> tuple[int, int, int]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    passed = int(report.get("numPassedTests", 0))
    failed = int(report.get("numFailedTests", 0))
    skipped = int(report.get("numPendingTests", 0)) + int(report.get("numTodoTests", 0))
    return passed, failed, skipped


def _parse_pytest_xml(report_path: Path) -> tuple[int, int, int]:
    root = ET.fromstring(report_path.read_text(encoding="utf-8"))
    tests = 0
    failures = 0
    errors = 0
    skipped = 0

    if root.tag == "testsuite":
        tests = int(root.attrib.get("tests", 0))
        failures = int(root.attrib.get("failures", 0))
        errors = int(root.attrib.get("errors", 0))
        skipped = int(root.attrib.get("skipped", 0))
    elif root.tag == "testsuites":
        suites = list(root.findall("testsuite"))
        if suites:
            for suite in suites:
                tests += int(suite.attrib.get("tests", 0))
                failures += int(suite.attrib.get("failures", 0))
                errors += int(suite.attrib.get("errors", 0))
                skipped += int(suite.attrib.get("skipped", 0))
        else:
            tests = int(root.attrib.get("tests", 0))
            failures = int(root.attrib.get("failures", 0))
            errors = int(root.attrib.get("errors", 0))
            skipped = int(root.attrib.get("skipped", 0))

    passed = tests - failures - errors - skipped
    return passed, failures + errors, skipped


def _extract_json_blob(raw: str) -> dict[str, Any]:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Could not find JSON object in Playwright output")
    return json.loads(raw[start : end + 1])


def _stable_layer_projection(result: LayerResult) -> dict[str, int | None]:
    return {
        "exit_code": result.exit_code,
        "passed": result.passed,
        "failed": result.failed,
        "skipped": result.skipped,
        "retries": result.retries,
    }


def build_determinism_signature(
    results: dict[str, LayerResult],
) -> tuple[dict[str, dict[str, int | None]], str]:
    stable_projection = {
        layer: _stable_layer_projection(result)
        for layer, result in sorted(results.items())
    }
    stable_json = json.dumps(stable_projection, sort_keys=True, separators=(",", ":"))
    signature = hashlib.sha256(stable_json.encode("utf-8")).hexdigest()
    return stable_projection, signature


def _resolve_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return ROOT / path


def _resolve_project_python() -> str:
    venv_python = ROOT / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def _read_signature(summary_path: Path) -> str:
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    signature = payload.get("determinism", {}).get("signature_sha256")
    if not isinstance(signature, str) or not signature:
        raise ValueError(f"Missing determinism.signature_sha256 in {summary_path}")
    return signature


def _parse_playwright_json(raw: str) -> tuple[int, int, int, int]:
    report = _extract_json_blob(raw)
    stats = report.get("stats", {})
    passed = int(stats.get("expected", 0))
    failed = int(stats.get("unexpected", 0))
    skipped = int(stats.get("skipped", 0))
    retries = int(stats.get("flaky", 0))
    return passed, failed, skipped + retries, retries


def run_harness(output_dir: Path) -> tuple[dict[str, LayerResult], bool]:
    output_dir.mkdir(parents=True, exist_ok=True)

    vitest_json = output_dir / "vitest-report.json"
    pytest_xml = output_dir / "pytest-report.xml"
    backend_python = _resolve_project_python()
    backend_pythonpath = os.pathsep.join(
        [
            str(ROOT),
            str(ROOT / "src"),
            *([os.environ["PYTHONPATH"]] if os.environ.get("PYTHONPATH") else []),
        ]
    )

    layers: list[tuple[str, list[str], dict[str, str] | None]] = [
        ("typescript", ["npm", "run", "tsc"], None),
        (
            "frontend_unit",
            [
                "npm",
                "run",
                "vitest",
                "--",
                "--reporter=json",
                "--outputFile",
                str(vitest_json),
            ],
            None,
        ),
        (
            "backend_unit",
            [backend_python, "-m", "pytest", "-q", "--junitxml", str(pytest_xml)],
            {"PYTHONPATH": backend_pythonpath},
        ),
        ("e2e", ["npm", "run", "playwright", "--", "--reporter=json"], None),
    ]

    results: dict[str, LayerResult] = {}

    for layer, command, env_overrides in layers:
        log_path = output_dir / f"{layer}.log"
        proc, duration_ms = _run_command(command, log_path, env_overrides)
        result = LayerResult(
            layer=layer,
            command=" ".join(command),
            exit_code=proc.returncode,
            duration_ms=duration_ms,
            log_path=str(log_path.relative_to(ROOT)),
        )

        if layer == "frontend_unit" and vitest_json.exists():
            passed, failed, skipped = _parse_vitest_json(vitest_json)
            result.passed = passed
            result.failed = failed
            result.skipped = skipped
        elif layer == "backend_unit" and pytest_xml.exists():
            passed, failed, skipped = _parse_pytest_xml(pytest_xml)
            result.passed = passed
            result.failed = failed
            result.skipped = skipped
        elif layer == "e2e":
            try:
                passed, failed, skipped_total, retries = _parse_playwright_json(
                    proc.stdout
                )
            except Exception as exc:  # pragma: no cover - defensive parser fallback
                result.details["parse_error"] = str(exc)
            else:
                result.passed = passed
                result.failed = failed
                result.skipped = skipped_total - retries
                result.retries = retries

        results[layer] = result

        if proc.returncode != 0:
            break

    all_green = True
    required_layers = ["typescript", "frontend_unit", "backend_unit", "e2e"]
    for layer in required_layers:
        result = results.get(layer)
        if result is None:
            all_green = False
            continue
        if result.exit_code != 0:
            all_green = False
        if layer != "typescript":
            if result.failed != 0 or result.skipped != 0 or result.retries != 0:
                all_green = False

    return results, all_green


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Meridian deterministic test harness"
    )
    parser.add_argument(
        "--output-dir",
        default=str(HARNESS_ROOT / _utc_now()),
        help="Directory for harness logs and summary",
    )
    parser.add_argument(
        "--baseline-summary",
        default="",
        help="Optional baseline summary.json path for repeat-run signature comparison",
    )
    args = parser.parse_args()

    output_dir = _resolve_path(args.output_dir)

    results, all_green = run_harness(output_dir)
    stable_projection, determinism_signature = build_determinism_signature(results)

    baseline_signature: str | None = None
    match_baseline: bool | None = None
    baseline_summary_rel: str | None = None
    if args.baseline_summary:
        baseline_summary_path = _resolve_path(args.baseline_summary)
        baseline_summary_rel = str(baseline_summary_path.relative_to(ROOT))
        baseline_signature = _read_signature(baseline_summary_path)
        match_baseline = determinism_signature == baseline_signature

    final_green = all_green and (match_baseline is not False)

    summary = {
        "generated_at": _utc_now(),
        "output_dir": str(output_dir.relative_to(ROOT)),
        "all_green": final_green,
        "test_layers_green": all_green,
        "layers": {name: asdict(result) for name, result in results.items()},
        "determinism": {
            "stable_projection": stable_projection,
            "signature_sha256": determinism_signature,
            "baseline_summary": baseline_summary_rel,
            "baseline_signature_sha256": baseline_signature,
            "baseline_match": match_baseline,
        },
        "requirements": {
            "typescript_errors": 0,
            "frontend_failed": 0,
            "frontend_skipped": 0,
            "backend_failed": 0,
            "backend_skipped": 0,
            "e2e_failed": 0,
            "e2e_skipped": 0,
            "e2e_retries": 0,
        },
    }
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2))
    return 0 if final_green else 1


if __name__ == "__main__":
    raise SystemExit(main())
