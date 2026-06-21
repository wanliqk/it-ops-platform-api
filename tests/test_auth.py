from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app


def test_logout_with_valid_token() -> None:
    client = TestClient(app)
    token = create_access_token("1")

    response = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {
        "message": "Logout successful. Please clear the local access token."
    }


def test_logout_rejects_invalid_token() -> None:
    client = TestClient(app)

    response = client.post("/api/v1/auth/logout", headers={"Authorization": "Bearer invalid"})

    assert response.status_code == 401
