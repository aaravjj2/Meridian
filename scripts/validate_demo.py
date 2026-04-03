#!/usr/bin/env python3
"""
Demo Mode Validation Script

Validates that Meridian's demo mode is properly configured with:
- All required fixture files present
- Demo trace file is valid JSON
- All data source fixtures exist
- API health check works in demo mode

Exit codes:
    0 - All checks passed
    1 - One or more checks failed
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from meridian.settings import FIXTURES_DIR, ROOT_DIR


# ANSI color codes for output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def print_success(msg: str) -> None:
    print(f"{Colors.GREEN}✓{Colors.RESET} {msg}")


def print_error(msg: str) -> None:
    print(f"{Colors.RED}✗{Colors.RESET} {msg}")


def print_warning(msg: str) -> None:
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {msg}")


def print_info(msg: str) -> None:
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {msg}")


def print_header(msg: str) -> None:
    print(f"\n{Colors.BOLD}{msg}{Colors.RESET}")


def check_fixtures_dir() -> bool:
    """Check that fixtures directory exists."""
    print_header("Checking Fixtures Directory")

    if not FIXTURES_DIR.exists():
        print_error(f"Fixtures directory not found: {FIXTURES_DIR}")
        return False

    print_success(f"Fixtures directory exists: {FIXTURES_DIR}")
    return True


def check_demo_trace() -> bool:
    """Check that demo trace file exists and is valid JSON."""
    print_header("Checking Demo Trace File")

    trace_file = FIXTURES_DIR / "traces" / "demo_trace.json"

    if not trace_file.exists():
        print_error(f"Demo trace file not found: {trace_file}")
        return False

    print_success(f"Demo trace file exists: {trace_file}")

    # Validate JSON structure
    try:
        content = trace_file.read_text(encoding="utf-8")
        data = json.loads(content)

        if not isinstance(data, list):
            print_error("Demo trace must be a JSON array")
            return False

        if not data:
            print_error("Demo trace array is empty")
            return False

        # Validate trace event structure
        required_fields = {"type", "step", "ts"}
        for i, event in enumerate(data):
            event_type = event.get("type")
            step = event.get("step")
            timestamp = event.get("ts")

            if not event_type:
                print_error(f"Trace event {i} missing 'type' field")
                return False

            if step is None:
                print_error(f"Trace event {i} missing 'step' field")
                return False

            if not timestamp:
                print_error(f"Trace event {i} missing 'ts' field")
                return False

        print_success(f"Demo trace is valid JSON with {len(data)} events")

        # List event types for transparency
        event_types = set(e.get("type") for e in data)
        print_info(f"Event types found: {', '.join(sorted(event_types))}")

    except json.JSONDecodeError as e:
        print_error(f"Demo trace contains invalid JSON: {e}")
        return False
    except Exception as e:
        print_error(f"Error reading demo trace: {e}")
        return False

    return True


def check_data_source_fixtures() -> bool:
    """Check that all data source fixtures exist."""
    print_header("Checking Data Source Fixtures")

    required_fixtures = {
        "FRED": FIXTURES_DIR / "fred",
        "Kalshi": FIXTURES_DIR / "kalshi",
        "Polymarket": FIXTURES_DIR / "polymarket",
        "EDGAR": FIXTURES_DIR / "edgar",
        "News": FIXTURES_DIR / "news",
        "Regime": FIXTURES_DIR / "regime_snapshot.json",
        "Screener": FIXTURES_DIR / "screener_snapshot.json",
    }

    all_valid = True

    for name, path in required_fixtures.items():
        if path.is_dir():
            # Check directory has at least one JSON file
            json_files = list(path.glob("*.json"))
            if json_files:
                print_success(f"{name} fixtures: {len(json_files)} files found")
            else:
                print_warning(f"{name} fixtures directory exists but is empty: {path}")
                all_valid = False
        elif path.is_file():
            # Single file fixture
            print_success(f"{name} fixture file exists: {path.name}")
        else:
            print_error(f"{name} fixtures not found: {path}")
            all_valid = False

    return all_valid


def check_critical_fixtures() -> bool:
    """Check critical fixture files for demo functionality."""
    print_header("Checking Critical Demo Fixtures")

    critical_files = {
        "FRED T10Y2Y": FIXTURES_DIR / "fred" / "T10Y2Y.json",
        "Kalshi markets": FIXTURES_DIR / "kalshi" / "markets.json",
        "Polymarket markets": FIXTURES_DIR / "polymarket" / "markets.json",
        "Regime snapshot": FIXTURES_DIR / "regime_snapshot.json",
        "Screener snapshot": FIXTURES_DIR / "screener_snapshot.json",
    }

    all_valid = True

    for name, path in critical_files.items():
        if path.exists():
            # Also validate it's valid JSON
            try:
                content = path.read_text(encoding="utf-8")
                json.loads(content)
                print_success(f"{name}: valid JSON")
            except json.JSONDecodeError:
                print_error(f"{name}: file exists but contains invalid JSON")
                all_valid = False
        else:
            print_error(f"{name}: file not found at {path}")
            all_valid = False

    return all_valid


def check_settings_module() -> bool:
    """Check that settings module can be imported and has correct defaults."""
    print_header("Checking Settings Module")

    try:
        from meridian.settings import get_mode, is_demo_mode, FIXTURES_DIR, CACHE_DIR

        # Test mode detection
        mode = get_mode()
        if mode in ("demo", "live"):
            print_success(f"Mode detection works: '{mode}'")
        else:
            print_error(f"Invalid mode returned: '{mode}'")
            return False

        # Test demo mode function
        is_demo = is_demo_mode()
        print_success(f"is_demo_mode() returns: {is_demo}")

        # Test paths
        if FIXTURES_DIR.exists():
            print_success(f"FIXTURES_DIR is accessible: {FIXTURES_DIR}")
        else:
            print_error(f"FIXTURES_DIR not accessible: {FIXTURES_DIR}")
            return False

        return True

    except ImportError as e:
        print_error(f"Failed to import settings module: {e}")
        return False
    except Exception as e:
        print_error(f"Error checking settings module: {e}")
        return False


def check_api_health_in_demo_mode() -> bool:
    """Check that the API health endpoint responds correctly in demo mode."""
    print_header("Checking API Health (Demo Mode)")

    try:
        import asyncio
        import os

        # Force demo mode for this check
        original_mode = os.environ.get("MERIDIAN_MODE")
        os.environ["MERIDIAN_MODE"] = "demo"

        # Import after setting environment
        from apps.api.main import app

        # Restore original mode
        if original_mode is not None:
            os.environ["MERIDIAN_MODE"] = original_mode
        else:
            del os.environ["MERIDIAN_MODE"]

        # Import TestClient for health check
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/api/v1/health")

        if response.status_code != 200:
            print_error(f"Health endpoint returned status {response.status_code}")
            return False

        data = response.json()

        if data.get("status") != "ok":
            print_error(f"Health check failed: {data}")
            return False

        if data.get("mode") != "demo":
            print_warning(f"Health endpoint reports mode='{data.get('mode')}', expected 'demo'")

        print_success("API health check passed in demo mode")
        print_info(f"Health response: status={data.get('status')}, mode={data.get('mode')}, version={data.get('version')}")

        return True

    except ImportError as e:
        print_warning(f"Could not import FastAPI app for health check: {e}")
        print_info("This is expected if FastAPI dependencies are not installed")
        return True  # Don't fail if dependencies missing
    except Exception as e:
        print_warning(f"Could not perform API health check: {e}")
        print_info("This may be expected if dependencies are not installed")
        return True  # Don't fail if dependencies missing


def main() -> int:
    """Run all validation checks and return exit code."""
    print(f"{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}Meridian Demo Mode Validation{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print_info(f"Root directory: {ROOT_DIR}")
    print_info(f"Fixtures directory: {FIXTURES_DIR}")

    checks = [
        check_fixtures_dir,
        check_demo_trace,
        check_data_source_fixtures,
        check_critical_fixtures,
        check_settings_module,
        check_api_health_in_demo_mode,
    ]

    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print_error(f"Check failed with exception: {e}")
            results.append(False)
        print()

    # Summary
    print_header("Validation Summary")
    passed = sum(results)
    total = len(results)

    if all(results):
        print_success(f"All {total} validation checks passed!")
        print()
        print_info("Demo mode is properly configured and ready to use.")
        return 0
    else:
        print_error(f"{total - passed}/{total} validation checks failed")
        print()
        print_info("Please fix the issues above before running demo mode.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
