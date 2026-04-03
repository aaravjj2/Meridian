from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROOF_ROOT = ROOT / "artifacts" / "proof"
HARNESS_ROOT = ROOT / "artifacts" / "harness"


@dataclass
class ManifestEntry:
    path: str
    sha256: str
    size: int


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_git(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"

def _git_dirty_info() -> tuple[bool, list[str]]:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
    except Exception:
        return True, ["unknown"]

    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return len(lines) > 0, lines


def _resolve_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return ROOT / path


def _copy_if_exists(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _latest_harness_summary() -> Path | None:
    summaries = sorted(
        HARNESS_ROOT.glob("*/summary.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return summaries[0] if summaries else None


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_inventory(base_dir: Path) -> list[ManifestEntry]:
    entries: list[ManifestEntry] = []
    for path in sorted(base_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(base_dir).as_posix()
        if rel == "MANIFEST.md":
            continue
        entries.append(
            ManifestEntry(
                path=rel,
                sha256=_sha256_file(path),
                size=path.stat().st_size,
            )
        )
    return entries


def _deployment_status_from_repo() -> tuple[str, list[str]]:
    evidence: list[str] = []
    vercel_path = ROOT / "vercel.json"
    if vercel_path.exists():
        evidence.append("vercel.json")
        try:
            payload = _read_json(vercel_path)
            env = payload.get("env", {})
            api_base = env.get("MERIDIAN_API_BASE_URL", "(unset)")
            return (
                f"Vercel config present; frontend rewrite target configured via MERIDIAN_API_BASE_URL={api_base}.",
                evidence,
            )
        except Exception:
            return ("Vercel config present but could not be parsed.", evidence)
    return ("No deployment configuration file discovered.", evidence)


def _collect_artifacts(out_dir: Path, harness_summary: dict[str, Any]) -> None:
    test_results_dir = out_dir / "test-results"
    screenshots_dir = out_dir / "screenshots"
    deployment_dir = out_dir / "deployment"
    test_results_dir.mkdir(parents=True, exist_ok=True)
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    deployment_dir.mkdir(parents=True, exist_ok=True)

    harness_out_rel = harness_summary.get("output_dir", "")
    harness_out_dir = ROOT / harness_out_rel if harness_out_rel else None

    if harness_out_dir and harness_out_dir.exists():
        _copy_if_exists(harness_out_dir / "summary.json", test_results_dir / "harness-summary.json")
        for layer_name, layer in harness_summary.get("layers", {}).items():
            log_rel = layer.get("log_path")
            if isinstance(log_rel, str) and log_rel:
                _copy_if_exists(ROOT / log_rel, test_results_dir / f"{layer_name}.log")

    _copy_if_exists(ROOT / "playwright-report", out_dir / "playwright-report")
    _copy_if_exists(ROOT / "test-results", out_dir / "test-results" / "playwright")
    _copy_if_exists(ROOT / "screenshots", out_dir / "screenshots")
    _copy_if_exists(ROOT / "artifacts" / "TOUR.webm", out_dir / "TOUR.webm")

    _copy_if_exists(ROOT / "vercel.json", deployment_dir / "vercel.json")
    _copy_if_exists(ROOT / ".github" / "workflows" / "ci.yml", deployment_dir / "ci.yml")


def _extract_commands(harness_summary: dict[str, Any], extra_commands: list[str]) -> list[str]:
    commands: list[str] = []
    for layer in ["typescript", "frontend_unit", "backend_unit", "e2e"]:
        layer_payload = harness_summary.get("layers", {}).get(layer, {})
        command = layer_payload.get("command")
        if isinstance(command, str) and command:
            commands.append(command)

    for cmd in extra_commands:
        if cmd.strip():
            commands.append(cmd.strip())

    deduped: list[str] = []
    seen: set[str] = set()
    for cmd in commands:
        if cmd not in seen:
            deduped.append(cmd)
            seen.add(cmd)
    return deduped


def _extract_results(harness_summary: dict[str, Any]) -> dict[str, Any]:
    layers = harness_summary.get("layers", {})
    return {
        "all_green": harness_summary.get("all_green"),
        "test_layers_green": harness_summary.get("test_layers_green"),
        "layers": {
            name: {
                "exit_code": payload.get("exit_code"),
                "passed": payload.get("passed"),
                "failed": payload.get("failed"),
                "skipped": payload.get("skipped"),
                "retries": payload.get("retries"),
                "duration_ms": payload.get("duration_ms"),
            }
            for name, payload in layers.items()
        },
        "requirements": harness_summary.get("requirements", {}),
        "determinism_signature_sha256": harness_summary.get("determinism", {}).get("signature_sha256"),
    }


def _write_readme(out_dir: Path, payload: dict[str, Any]) -> None:
    content = "\n".join(
        [
            "# Proof Pack",
            "",
            f"- Slug: {payload['slug']}",
            f"- Generated at (UTC): {payload['generated_at']}",
            f"- Git SHA: {payload['git_sha']}",
            f"- Git branch: {payload['git_branch']}",
            f"- Harness summary source: {payload['harness_summary']}",
            f"- Git dirty: {payload['git_dirty']}",
            "",
            "This proof pack is generated automatically to reduce manual drift between docs, validation output, and shipped artifacts.",
        ]
    )
    (out_dir / "README.md").write_text(content + "\n", encoding="utf-8")


def _write_manifest_json(out_dir: Path, payload: dict[str, Any], entries: list[ManifestEntry]) -> None:
    data = dict(payload)
    data["files"] = [asdict(entry) for entry in entries]
    (out_dir / "manifest.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _write_manifest_md(out_dir: Path, payload: dict[str, Any], entries: list[ManifestEntry]) -> None:
    results = payload["results"]
    lines: list[str] = [
        "# Milestone Manifest",
        "",
        "## Objective",
        payload["objective"],
        "",
        "## Scope",
    ]

    scope_items = payload.get("scope", [])
    if scope_items:
        for item in scope_items:
            lines.append(f"- {item}")
    else:
        lines.append("- Repository truth-tightening alignment pass.")

    lines.extend(
        [
            "",
            "## Metadata",
            f"- Generated at (UTC): {payload['generated_at']}",
            f"- Git SHA: {payload['git_sha']}",
            f"- Git branch: {payload['git_branch']}",
            f"- Git dirty: {payload['git_dirty']}",
            f"- Harness summary: {payload['harness_summary']}",
        ]
    )

    dirty_files = payload.get("git_dirty_files", [])
    if dirty_files:
        lines.extend(["", "## Git Dirty Files"])
        for dirty in dirty_files:
            lines.append(f"- {dirty}")

    lines.extend(["", "## Exact Commands Run", "```bash"])

    for command in payload["commands_run"]:
        lines.append(command)

    lines.extend(["```", "", "## Exact Results"])

    lines.append(f"- all_green: {results.get('all_green')}")
    lines.append(f"- test_layers_green: {results.get('test_layers_green')}")

    for layer_name in ["typescript", "frontend_unit", "backend_unit", "e2e"]:
        layer = results.get("layers", {}).get(layer_name)
        if not layer:
            continue
        lines.append(
            "- "
            + f"{layer_name}: exit={layer.get('exit_code')}, passed={layer.get('passed')}, "
            + f"failed={layer.get('failed')}, skipped={layer.get('skipped')}, retries={layer.get('retries')}"
        )

    lines.append(f"- determinism_signature_sha256: {results.get('determinism_signature_sha256')}")

    lines.extend(["", "## Root Causes If Fixes Were Needed"])
    root_causes = payload.get("root_causes", [])
    if root_causes:
        for cause in root_causes:
            lines.append(f"- {cause}")
    else:
        lines.append("- None in this run.")

    lines.extend(["", "## File Inventory"])
    for entry in entries:
        lines.append(f"- {entry.path} ({entry.size} bytes)")

    lines.extend(["", "## Known Limitations"])
    limitations = payload.get("known_limitations", [])
    if limitations:
        for limitation in limitations:
            lines.append(f"- {limitation}")
    else:
        lines.append("- Deployment reachability is not actively probed by this script.")

    lines.extend(["", "## Current Deployment Status", payload["deployment_status"], ""])

    lines.extend(
        [
            "## SHA256 Checksums",
            "| File | SHA256 | Size (bytes) |",
            "|---|---|---:|",
        ]
    )

    for entry in entries:
        lines.append(f"| {entry.path} | {entry.sha256} | {entry.size} |")

    (out_dir / "MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Meridian proof pack")
    parser.add_argument("slug", help="Proof slug suffix")
    parser.add_argument(
        "--objective",
        default="Truth-tightening audit pass to align code, docs, validation gates, and deployment narrative.",
        help="Objective text included in manifest",
    )
    parser.add_argument("--scope", action="append", default=[], help="Scope bullet (repeatable)")
    parser.add_argument("--root-cause", action="append", default=[], help="Root-cause bullet (repeatable)")
    parser.add_argument(
        "--known-limitation",
        action="append",
        default=[],
        help="Known limitation bullet (repeatable)",
    )
    parser.add_argument("--deployment-status", default="", help="Deployment status text override")
    parser.add_argument("--harness-summary", default="", help="Path to harness summary.json")
    parser.add_argument("--command", action="append", default=[], help="Additional command for manifest")
    args = parser.parse_args()

    harness_summary_path = (
        _resolve_path(args.harness_summary) if args.harness_summary else _latest_harness_summary()
    )
    if harness_summary_path is None or not harness_summary_path.exists():
        print("No harness summary found. Run scripts/test_harness.py first or pass --harness-summary.")
        return 1

    harness_summary = _read_json(harness_summary_path)

    created_at = _utc_now()
    out_dir = PROOF_ROOT / f"{created_at}-{args.slug.strip()}"
    out_dir.mkdir(parents=True, exist_ok=False)

    _collect_artifacts(out_dir, harness_summary)

    deployment_status, deployment_evidence = _deployment_status_from_repo()
    if args.deployment_status.strip():
        deployment_status = args.deployment_status.strip()

    payload: dict[str, Any] = {
        "slug": args.slug.strip(),
        "generated_at": created_at,
        "git_sha": _run_git("rev-parse", "HEAD"),
        "git_branch": _run_git("branch", "--show-current"),
        "git_dirty": _git_dirty_info()[0],
        "git_dirty_files": _git_dirty_info()[1],
        "objective": args.objective.strip(),
        "scope": args.scope,
        "commands_run": _extract_commands(harness_summary, args.command),
        "results": _extract_results(harness_summary),
        "root_causes": args.root_cause,
        "known_limitations": args.known_limitation,
        "deployment_status": deployment_status,
        "deployment_evidence": deployment_evidence,
        "harness_summary": str(harness_summary_path.relative_to(ROOT)),
    }

    _write_readme(out_dir, payload)

    # First pass to create manifest.json for inventory hashing.
    _write_manifest_json(out_dir, payload, entries=[])

    entries = _build_inventory(out_dir)
    _write_manifest_json(out_dir, payload, entries)

    # Rebuild inventory to capture final manifest.json hash and write MANIFEST.md.
    entries = _build_inventory(out_dir)
    _write_manifest_md(out_dir, payload, entries)

    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
