from __future__ import annotations

import hashlib
import json
import shutil
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROOF_ROOT = ROOT / "artifacts" / "proof"


@dataclass
class ManifestEntry:
    path: str
    sha256: str
    size: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def copy_if_exists(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_screenshot_if_exists(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def build_manifest(base_dir: Path) -> list[ManifestEntry]:
    entries: list[ManifestEntry] = []
    for path in sorted(base_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(base_dir).as_posix()
        entries.append(ManifestEntry(path=rel, sha256=sha256_file(path), size=path.stat().st_size))
    return entries


def write_manifest_md(out_dir: Path, entries: list[ManifestEntry]) -> None:
    lines = [
        "# Proof Pack Manifest",
        "",
        "| File | SHA256 | Size (bytes) |",
        "|---|---|---:|",
    ]
    for entry in entries:
        lines.append(f"| `{entry.path}` | `{entry.sha256}` | {entry.size} |")
    (out_dir / "MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_readme(out_dir: Path, slug: str, created_at: str) -> None:
    content = f"""# Proof Pack\n\n- Milestone: `{slug}`\n- Generated at (UTC): `{created_at}`\n- Root: `artifacts/proof/{out_dir.name}`\n\n## Included\n\n- `MANIFEST.md`\n- `manifest.json`\n- `test-results/`\n- `screenshots/`\n\nPlaywright report and TOUR recording are included when available for E2E milestones.\n"""
    (out_dir / "README.md").write_text(content, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/proof.py <milestone-slug>")
        return 1

    slug = sys.argv[1].strip()
    if not slug:
        print("Milestone slug is required")
        return 1

    created_at = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    out_dir = PROOF_ROOT / f"{created_at}-{slug}"
    out_dir.mkdir(parents=True, exist_ok=False)

    (out_dir / "test-results").mkdir(parents=True, exist_ok=True)
    (out_dir / "screenshots").mkdir(parents=True, exist_ok=True)

    ensure_file(out_dir / "test-results" / "README.txt", "Place milestone test outputs in this directory.\n")
    ensure_file(out_dir / "screenshots" / "README.txt", "Place milestone screenshots in this directory.\n")

    copy_if_exists(ROOT / "playwright-report", out_dir / "playwright-report")
    copy_if_exists(ROOT / "test-results", out_dir / "test-results" / "playwright")
    copy_if_exists(ROOT / "artifacts" / "TOUR.webm", out_dir / "TOUR.webm")

    copy_screenshot_if_exists(
        ROOT / "test-results" / "test_smoke-smoke-homepage-chrome-renders" / "test-finished-1.png",
        out_dir / "screenshots" / "homepage.png",
    )
    copy_screenshot_if_exists(
        ROOT / "test-results" / "test_research_flow-research-flow-query-to-complete-brief" / "test-finished-1.png",
        out_dir / "screenshots" / "brief-complete.png",
    )
    copy_screenshot_if_exists(
        ROOT / "test-results" / "test_screener-screener-loads-sorts-filters-opens-drawer" / "test-finished-1.png",
        out_dir / "screenshots" / "screener.png",
    )

    write_readme(out_dir, slug, created_at)

    entries = build_manifest(out_dir)
    manifest_json = [
        {"path": entry.path, "sha256": entry.sha256, "size": entry.size}
        for entry in entries
    ]
    (out_dir / "manifest.json").write_text(
        json.dumps(
            {
                "slug": slug,
                "generated_at": created_at,
                "files": manifest_json,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    entries = build_manifest(out_dir)
    write_manifest_md(out_dir, entries)

    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
