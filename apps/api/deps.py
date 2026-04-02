from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def get_mode() -> str:
    mode = os.getenv("MERIDIAN_MODE", "demo").strip().lower()
    if mode not in {"demo", "live"}:
        return "demo"
    return mode


def is_demo_mode() -> bool:
    return get_mode() == "demo"


def fixtures_dir() -> Path:
    return PROJECT_ROOT / "data" / "fixtures"
