from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_create_and_get_hand():
    response = client.post("/hands/", json=["call", "fold"])
    assert response.status_code == 200
    hand = response.json()
    hand_id = hand["id"]

    get_response = client.get(f"/hands/{hand_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == hand_id