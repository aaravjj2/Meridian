from __future__ import annotations

import logging
import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
FIXTURES_DIR = ROOT_DIR / "data" / "fixtures"
CACHE_DIR = ROOT_DIR / "data" / "cache"

# Configure logging for the module
logger = logging.getLogger(__name__)


# Valid mode values
VALID_MODES = {"demo", "live"}


def get_mode() -> str:
    """
    Get the Meridian runtime mode from environment.

    Returns:
        "demo" or "live". Defaults to "demo" if MERIDIAN_MODE is not set
        or contains an invalid value.

    Environment:
        MERIDIAN_MODE: "demo" (default) or "live"

    Examples:
        >>> get_mode()
        'demo'
        >>> os.environ['MERIDIAN_MODE'] = 'live'
        >>> get_mode()
        'live'
        >>> os.environ['MERIDIAN_MODE'] = 'invalid'
        >>> get_mode()  # doctest: +SKIP
        'demo'
    """
    mode = os.getenv("MERIDIAN_MODE", "demo").strip().lower()

    # Handle empty string case
    if not mode:
        logger.warning("MERIDIAN_MODE is set to empty string, defaulting to 'demo'")
        return "demo"

    if mode in VALID_MODES:
        return mode

    # Invalid mode - log warning and fall back to demo
    logger.warning(
        f"Invalid MERIDIAN_MODE value: '{mode}'. "
        f"Valid values are: {', '.join(sorted(VALID_MODES))}. "
        "Defaulting to 'demo' mode."
    )
    return "demo"


def is_demo_mode() -> bool:
    """
    Check if Meridian is running in demo mode.

    Returns:
        True if in demo mode (or if mode is invalid/unset), False only for live mode.

    Examples:
        >>> is_demo_mode()  # Assuming MERIDIAN_MODE is not set
        True
        >>> os.environ['MERIDIAN_MODE'] = 'live'
        >>> is_demo_mode()
        False
    """
    return get_mode() == "demo"
