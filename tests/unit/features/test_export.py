from __future__ import annotations

from pathlib import Path

from meridian.features.export import export_feature_snapshot


def test_export_feature_snapshot_writes_outputs(tmp_path: Path) -> None:
    parquet_path, json_path = export_feature_snapshot(tmp_path / "run1")
    assert parquet_path.exists()
    assert json_path.exists()


def test_export_is_byte_deterministic(tmp_path: Path) -> None:
    run1 = tmp_path / "run1"
    run2 = tmp_path / "run2"

    p1, j1 = export_feature_snapshot(run1)
    p2, j2 = export_feature_snapshot(run2)

    assert p1.read_bytes() == p2.read_bytes()
    assert j1.read_bytes() == j2.read_bytes()
