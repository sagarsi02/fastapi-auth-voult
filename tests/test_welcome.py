from fastapi.testclient import TestClient


def test_welcome_route(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Greet": "Welcome to Our Landing Page - Auth Voult"}
