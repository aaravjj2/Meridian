from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.main import app


client = TestClient(app)


def test_regime_endpoint_shape() -> None:
    response = client.get("/api/v1/regime")
    assert response.status_code == 200

    payload = response.json()
    dims = payload["dimensions"]
    assert set(dims.keys()) == {"growth", "inflation", "monetary", "credit", "labor"}
    assert all(isinstance(dims[key], str) and dims[key] for key in dims)
    assert isinstance(payload["narrative"], str) and payload["narrative"]
