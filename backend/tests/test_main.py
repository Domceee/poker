from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_root_redirect():
    response = client.get("/")
    assert response.status_code in [200, 307, 308]