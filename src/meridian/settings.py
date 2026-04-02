from __future__ import annotations

import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
FIXTURES_DIR = ROOT_DIR / "data" / "fixtures"
CACHE_DIR = ROOT_DIR / "data" / "cache"


def get_mode() -> str:
    mode = os.getenv("MERIDIAN_MODE", "demo").strip().lower()
    if mode in {"demo", "live"}:
        return mode
    return "demo"


def is_demo_mode() -> bool:
    return get_mode() == "demo"
