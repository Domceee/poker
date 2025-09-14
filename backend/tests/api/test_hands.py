import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_start_game():
    response = client.post("/hands/start", json={"num_players": 6, "dealer_index": 0})
    assert response.status_code == 200
    data = response.json()
    assert "game_id" in data
    assert "log" in data
    assert isinstance(data["log"], list)