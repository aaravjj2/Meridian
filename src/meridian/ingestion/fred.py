from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
from pydantic import BaseModel

from meridian.settings import CACHE_DIR, FIXTURES_DIR, is_demo_mode


class FredSeriesMeta(BaseModel):
    series_id: str
    title: str
    frequency: str


@dataclass(slots=True)
class FredClient:
    api_key: str | None = None
    demo_mode: bool | None = None
    fixtures_root: Path = FIXTURES_DIR / "fred"
    cache_root: Path = CACHE_DIR / "fred"
    ttl_seconds: int = 3600

    def __post_init__(self) -> None:
        if self.demo_mode is None:
            self.demo_mode = is_demo_mode()
        self.cache_root.mkdir(parents=True, exist_ok=True)

    def fetch_series(self, series_id: str, start: str | None = None, end: str | None = None) -> pd.DataFrame:
        if self.demo_mode:
            payload = self._load_fixture(series_id)
            return self._to_dataframe(payload)

        cache_payload = self._read_cache(series_id)
        if cache_payload is not None:
            return self._to_dataframe(cache_payload)

        payload = self._fetch_live(series_id, start=start, end=end)
        self._write_cache(series_id, payload)
        return self._to_dataframe(payload)

    def search(self, query: str, limit: int = 10) -> list[FredSeriesMeta]:
        records = []
        q = query.strip().lower()
        for path in sorted(self.fixtures_root.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            title = str(payload.get("name", path.stem))
            series_id = str(payload.get("series_id", path.stem))
            frequency = str(payload.get("frequency", "Unknown"))
            if q in series_id.lower() or q in title.lower():
                records.append(FredSeriesMeta(series_id=series_id, title=title, frequency=frequency))
        return records[:limit]

    def _load_fixture(self, series_id: str) -> dict[str, Any]:
        fixture_path = self.fixtures_root / f"{series_id}.json"
        if not fixture_path.exists():
            raise FileNotFoundError(f"FRED fixture not found: {fixture_path}")
        return json.loads(fixture_path.read_text(encoding="utf-8"))

    def _to_dataframe(self, payload: dict[str, Any]) -> pd.DataFrame:
        observations = payload.get("observations", [])
        rows: list[dict[str, Any]] = []
        for row in observations:
            value_raw = row.get("value")
            try:
                value = float(value_raw)
            except (TypeError, ValueError):
                continue
            rows.append({"date": row.get("date"), "value": value})
        df = pd.DataFrame(rows)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)
        return df

    def _fetch_live(self, series_id: str, start: str | None, end: str | None) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("FRED API key is required for live mode")

        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
        }
        if start:
            params["observation_start"] = start
        if end:
            params["observation_end"] = end

        response = httpx.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params=params,
            timeout=30.0,
        )
        response.raise_for_status()
        payload = response.json()
        return {
            "series_id": series_id,
            "name": series_id,
            "frequency": "Unknown",
            "observations": payload.get("observations", []),
        }

    def _cache_paths(self, series_id: str) -> tuple[Path, Path]:
        data_path = self.cache_root / f"{series_id}.json"
        meta_path = self.cache_root / f"{series_id}.meta.json"
        return data_path, meta_path

    def _read_cache(self, series_id: str) -> dict[str, Any] | None:
        data_path, meta_path = self._cache_paths(series_id)
        if not data_path.exists() or not meta_path.exists():
            return None

        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        expires_at = datetime.fromisoformat(metadata["expires_at"])
        if datetime.now(UTC) >= expires_at:
            return None

        return json.loads(data_path.read_text(encoding="utf-8"))

    def _write_cache(self, series_id: str, payload: dict[str, Any]) -> None:
        data_path, meta_path = self._cache_paths(series_id)
        data_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        expires_at = datetime.now(UTC) + timedelta(seconds=self.ttl_seconds)
        meta_path.write_text(
            json.dumps({"expires_at": expires_at.isoformat()}, indent=2) + "\n",
            encoding="utf-8",
        )
