from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.main import app


client = TestClient(app)


def test_screener_returns_sorted_contracts() -> None:
    response = client.get("/api/v1/screener")
    assert response.status_code == 200

    payload = response.json()
    contracts = payload["contracts"]
    assert len(contracts) >= 5
    assert payload["count"] == len(contracts)

    dislocations = [item["dislocation"] for item in contracts]
    assert dislocations == sorted(dislocations, reverse=True)


def test_screener_platform_filter() -> None:
    response = client.get("/api/v1/screener", params={"platform": "kalshi"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    assert all(item["platform"] == "kalshi" for item in payload["contracts"])
