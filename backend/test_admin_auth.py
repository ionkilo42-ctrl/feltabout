from fastapi.testclient import TestClient

import main


def test_admin_login_accepts_configured_credentials(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "local-admin-password")
    monkeypatch.setenv("JWT_SECRET", "test-secret")

    client = TestClient(main.app)

    response = client.post(
        "/auth/admin-login",
        json={"email": "admin@example.com", "password": "local-admin-password"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "admin"
    assert data["name"] == "Admin"
    assert isinstance(data["token"], str)

    me_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {data['token']}"},
    )

    assert me_response.status_code == 200
    assert me_response.json() == {
        "user_id": "admin",
        "email": "admin@example.com",
        "name": "Admin",
        "role": "admin",
    }


def test_admin_login_rejects_invalid_credentials(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "local-admin-password")

    client = TestClient(main.app)

    response = client.post(
        "/auth/admin-login",
        json={"email": "admin@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
