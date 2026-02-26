from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import src.api.routes.users as users_routes
from src.repositories.user_repository import UserRepository
from src.database.models import User


def _signup_payload(**overrides):
    payload = {
        "name": "Test User",
        "email": "Test@Example.com",
        "password": "StrongPassword123",
        "confirm_password": "StrongPassword123",
        "mobile_number": 9999999999,
        "city": "Test City",
    }
    payload.update(overrides)
    return payload


def _login_payload(**overrides):
    payload = {
        "email": "test@example.com",
        "password": "StrongPassword123",
    }
    payload.update(overrides)
    return payload


def _make_user() -> User:
    user = User(
        name="Test User",
        email="test@example.com",
        mobile_number=9999999999,
        city="Test City",
        password_hash="hashed",
    )
    user.id = uuid4()
    user.role = "user"
    user.is_active = True
    user.is_verified = False
    user.created_at = datetime.now(timezone.utc)
    return user


def test_register_user_success(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    async def fake_get_user_data_by_email(_session, _email, for_update=False):
        return None

    async def fake_create_user(_session, user):
        user.id = uuid4()
        user.created_at = datetime.now(timezone.utc)
        user.is_active = True
        user.is_verified = False
        return user

    monkeypatch.setattr(
        UserRepository, "get_user_data_by_email", fake_get_user_data_by_email
    )
    monkeypatch.setattr(UserRepository, "create_user", fake_create_user)
    monkeypatch.setattr(users_routes, "hash_password", lambda _pwd: "hashed")

    response = client.post("/users/register-user", json=_signup_payload())

    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "User registered successfully"
    assert data["email"] == "test@example.com"


def test_register_user_password_mismatch(client: TestClient):
    response = client.post(
        "/users/register-user",
        json=_signup_payload(confirm_password="WrongPassword"),
    )

    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "Passwords do not match"


def test_register_user_duplicate(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    async def fake_get_user_data_by_email(_session, _email, for_update=False):
        return _make_user()

    monkeypatch.setattr(
        UserRepository, "get_user_data_by_email", fake_get_user_data_by_email
    )

    response = client.post("/users/register-user", json=_signup_payload())

    assert response.status_code == 409
    assert response.json()["detail"]["message"] == "User already exists"


def test_login_user_success(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    user = _make_user()

    async def fake_get_user_data_by_email(_session, _email, for_update=False):
        return user

    async def fake_revoke_expired_refresh_tokens(_session, _now_utc):
        return None

    async def fake_count_active_refresh_tokens(_session, _user_id, _now_utc):
        return 0

    monkeypatch.setattr(
        UserRepository, "get_user_data_by_email", fake_get_user_data_by_email
    )
    monkeypatch.setattr(
        UserRepository,
        "revoke_expired_refresh_tokens",
        fake_revoke_expired_refresh_tokens,
    )
    monkeypatch.setattr(
        UserRepository, "count_active_refresh_tokens", fake_count_active_refresh_tokens
    )
    monkeypatch.setattr(users_routes, "verify_password", lambda _pwd, _hash: True)

    response = client.post("/users/login-user", json=_login_payload())

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["message"] == "User logged in successfully"


def test_login_user_invalid_credentials(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    user = _make_user()

    async def fake_get_user_data_by_email(_session, _email, for_update=False):
        return user

    monkeypatch.setattr(
        UserRepository, "get_user_data_by_email", fake_get_user_data_by_email
    )
    monkeypatch.setattr(users_routes, "verify_password", lambda _pwd, _hash: False)

    response = client.post("/users/login-user", json=_login_payload())

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_login_user_max_devices(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    user = _make_user()

    async def fake_get_user_data_by_email(_session, _email, for_update=False):
        return user

    async def fake_revoke_expired_refresh_tokens(_session, _now_utc):
        return None

    async def fake_count_active_refresh_tokens(_session, _user_id, _now_utc):
        return 5

    monkeypatch.setattr(
        UserRepository, "get_user_data_by_email", fake_get_user_data_by_email
    )
    monkeypatch.setattr(
        UserRepository,
        "revoke_expired_refresh_tokens",
        fake_revoke_expired_refresh_tokens,
    )
    monkeypatch.setattr(
        UserRepository, "count_active_refresh_tokens", fake_count_active_refresh_tokens
    )
    monkeypatch.setattr(users_routes, "verify_password", lambda _pwd, _hash: True)
    monkeypatch.setattr(users_routes.settings, "MAX_ACTIVE_DEVICES", 5)

    response = client.post("/users/login-user", json=_login_payload())

    assert response.status_code == 403
    assert "Maximum login limit" in response.json()["detail"]


def test_logout_user_success(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    refresh_obj = SimpleNamespace(is_revoked=False)

    async def fake_get_active_refresh_token(_session, _user_id, _hashed_token):
        return refresh_obj

    monkeypatch.setattr(
        UserRepository, "get_active_refresh_token", fake_get_active_refresh_token
    )

    response = client.post(
        "/users/logout-user", json={"refresh_token": "refresh-token-12345"}
    )

    assert response.status_code == 200
    assert response.json()["message"] == "User logged out successfully"
    assert refresh_obj.is_revoked is True


def test_logout_user_invalid_refresh_token(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    async def fake_get_active_refresh_token(_session, _user_id, _hashed_token):
        return None

    monkeypatch.setattr(
        UserRepository, "get_active_refresh_token", fake_get_active_refresh_token
    )

    response = client.post(
        "/users/logout-user", json={"refresh_token": "refresh-token-12345"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or revoked refresh token"


def test_refresh_token_success(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    now = datetime.now(timezone.utc)
    current_refresh = SimpleNamespace(
        session_expires_at=now + timedelta(days=2),
        device_info="ios",
        is_revoked=False,
    )

    async def fake_get_active_refresh_token(
        _session, _user_id, _hashed_token, now_utc=None, for_update=False
    ):
        return current_refresh

    monkeypatch.setattr(
        UserRepository, "get_active_refresh_token", fake_get_active_refresh_token
    )

    response = client.post("/users/get-access-token-from-refresh-token")

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]


def test_refresh_token_invalid(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    async def fake_get_active_refresh_token(
        _session, _user_id, _hashed_token, now_utc=None, for_update=False
    ):
        return None

    monkeypatch.setattr(
        UserRepository, "get_active_refresh_token", fake_get_active_refresh_token
    )

    response = client.post("/users/get-access-token-from-refresh-token")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or revoked refresh token"


def test_refresh_token_session_expired(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    current_refresh = SimpleNamespace(
        session_expires_at=datetime.now(timezone.utc) - timedelta(seconds=5),
        device_info="ios",
        is_revoked=False,
    )

    async def fake_get_active_refresh_token(
        _session, _user_id, _hashed_token, now_utc=None, for_update=False
    ):
        return current_refresh

    monkeypatch.setattr(
        UserRepository, "get_active_refresh_token", fake_get_active_refresh_token
    )

    response = client.post("/users/get-access-token-from-refresh-token")

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh session expired. Please login again."
