from fastapi.testclient import TestClient
import jwt
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.core.security import JWT_ALGORITHM
from app.core.database import Base, get_db
from app.main import app


def create_test_client() -> TestClient:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_register_user_success() -> None:
    client = create_test_client()

    response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "secure-password",
            "name": "Test User",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "user@example.com"
    assert data["name"] == "Test User"
    assert "id" in data
    assert "password_hash" not in data

    app.dependency_overrides.clear()


def test_register_duplicate_email_returns_conflict() -> None:
    client = create_test_client()

    payload = {
        "email": "user@example.com",
        "password": "secure-password",
        "name": "Test User",
    }

    first_response = client.post("/auth/register", json=payload)
    duplicate_response = client.post("/auth/register", json=payload)

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409

    app.dependency_overrides.clear()


def test_login_user_success(monkeypatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    client = create_test_client()

    register_payload = {
        "email": "user@example.com",
        "password": "secure-password",
        "name": "Test User",
    }
    register_response = client.post("/auth/register", json=register_payload)

    response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "secure-password",
        },
    )

    assert register_response.status_code == 201
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]

    payload = jwt.decode(
        data["access_token"],
        "test-secret",
        algorithms=[JWT_ALGORITHM],
    )
    assert payload["sub"] == register_response.json()["id"]
    assert payload["email"] == "user@example.com"
    assert "iat" in payload
    assert "exp" in payload

    app.dependency_overrides.clear()


def test_login_invalid_credentials_returns_generic_unauthorized(monkeypatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    client = create_test_client()

    response = client.post(
        "/auth/login",
        json={
            "email": "missing@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials."

    app.dependency_overrides.clear()


def test_refresh_rotates_refresh_token(monkeypatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    client = create_test_client()

    client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "secure-password",
            "name": "Test User",
        },
    )
    login_response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "secure-password",
            "device_id": "test-device",
        },
    )
    original_refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": original_refresh_token},
    )

    assert refresh_response.status_code == 200
    data = refresh_response.json()
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["refresh_token"] != original_refresh_token

    old_token_response = client.post(
        "/auth/refresh",
        json={"refresh_token": original_refresh_token},
    )
    assert old_token_response.status_code == 401

    app.dependency_overrides.clear()


def test_logout_deletes_refresh_token(monkeypatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    client = create_test_client()

    client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "secure-password",
            "name": "Test User",
        },
    )
    login_response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "secure-password",
        },
    )
    refresh_token = login_response.json()["refresh_token"]

    logout_response = client.post(
        "/auth/logout",
        json={"refresh_token": refresh_token},
    )
    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert logout_response.status_code == 204
    assert refresh_response.status_code == 401

    app.dependency_overrides.clear()
