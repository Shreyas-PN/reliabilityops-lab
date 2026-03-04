from fastapi.testclient import TestClient
from remediator.main import app

client = TestClient(app)


def test_webhook() -> None:
    response = client.post("/webhook", json={"incident_id": "INC-123"})
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
