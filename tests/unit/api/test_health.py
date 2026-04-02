from fastapi.testclient import TestClient

from apps.api.main import app


client = TestClient(app)


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["mode"] in {"demo", "live"}
    assert payload["version"] == "0.1.0"


def test_metadata_endpoint_returns_expected_shape() -> None:
    response = client.get("/api/v1/metadata")
    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "0.1.0"
    assert payload["model"] == "glm-5.1"
    assert payload["demo"] is True
    assert payload["data_sources"] == [
        "fred",
        "kalshi",
        "polymarket",
        "edgar",
        "news",
    ]
