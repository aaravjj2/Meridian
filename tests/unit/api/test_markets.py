from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.main import app


client = TestClient(app)


def test_markets_list_and_detail_and_explain() -> None:
    list_response = client.get("/api/v1/markets")
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["count"] >= 5

    first_market = list_payload["markets"][0]
    market_id = first_market["id"]

    detail_response = client.get(f"/api/v1/markets/{market_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == market_id

    explain_response = client.get(f"/api/v1/markets/{market_id}/explain")
    assert explain_response.status_code == 200
    explain_payload = explain_response.json()
    assert explain_payload["market_id"] == market_id
    assert "explanation" in explain_payload
