from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from meridian.features.compute import flatten_feature_snapshot
from meridian.ingestion.fred import FredClient


SERIES_FOR_FEATURES = ["T10Y2Y", "UNRATE", "CPIAUCSL", "FEDFUNDS", "BAMLH0A0HYM2"]


def export_feature_snapshot(output_dir: str | Path) -> tuple[Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    client = FredClient(demo_mode=True)
    all_series: dict[str, pd.DataFrame] = {}
    for series_id in SERIES_FOR_FEATURES:
        all_series[series_id] = client.fetch_series(series_id)

    snapshot = flatten_feature_snapshot(all_series)
    frame = pd.DataFrame([snapshot]).sort_index(axis=1)

    parquet_path = output / "features.parquet"
    json_path = output / "features.json"

    frame.to_parquet(parquet_path, index=False)
    json_path.write_text(json.dumps(snapshot, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    return parquet_path, json_path
