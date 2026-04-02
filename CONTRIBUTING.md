# Contributing

## Setup

1. Install Python 3.12 and Node.js 20+.
2. Create a Python virtual environment and install dependencies:
   - `pip install -e .[dev]`
3. Install Node dependencies:
   - `npm install`

## Dev loop

1. Run API: `uvicorn apps.api.main:app --reload --port 8000`
2. Run web: `npm run -w @meridian/web dev`
3. Run tests frequently:
   - `pytest -q`
   - `npm run tsc`
   - `npm run vitest`
   - `npm run playwright`

## Milestone gates

A milestone is complete only when:

1. Its required tests pass with zero failures.
2. A proof pack is generated via `python scripts/proof.py <milestone-slug>`.
3. The proof pack exists under `artifacts/proof/<ISO-timestamp>-<milestone-slug>/`.
