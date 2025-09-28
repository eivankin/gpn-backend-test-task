import datetime as dt

import fastapi
import jwt
import pytest
from httpx import AsyncClient

from app.error_messages import UserErrorMessages
from app.settings import settings


@pytest.fixture
def time_in_future() -> dt.datetime:
    return dt.datetime.now(dt.UTC) + dt.timedelta(days=1)


@pytest.fixture
def time_in_past() -> dt.datetime:
    return dt.datetime.now(dt.UTC) - dt.timedelta(days=1)


async def test_no_credentials(client: AsyncClient) -> None:
    response = await client.get("/api/notes/my/")
    assert response.status_code == fastapi.status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated"


async def test_invalid_token(client: AsyncClient) -> None:
    response = await client.get(
        "/api/notes/my/",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == fastapi.status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == UserErrorMessages.invalid_token


async def test_get_token(user_client: AsyncClient) -> None:
    response = await user_client.post(
        "/api/users/token/", data={"username": user_client.user.login, "password": "password"}
    )
    assert response.status_code == fastapi.status.HTTP_200_OK
    assert "access_token" in response.json()


async def test_get_token_for_nonexistent_user(client: AsyncClient) -> None:
    response = await client.post("/api/users/token/", data={"username": "nonexistent_user", "password": "password"})
    assert response.status_code == fastapi.status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == UserErrorMessages.wrong_login_pass


async def test_get_token_wrong_password(user_client: AsyncClient) -> None:
    response = await user_client.post(
        "/api/users/token/", data={"username": user_client.user.login, "password": "wrong_password"}
    )
    assert response.status_code == fastapi.status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == UserErrorMessages.wrong_login_pass


async def test_token_for_nonexistent_user(client: AsyncClient, time_in_future: dt.datetime) -> None:
    token = jwt.encode(
        {"sub": "nonexistent_user", "exp": time_in_future}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    response = await client.get(
        "/api/notes/my/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == fastapi.status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == UserErrorMessages.invalid_token


async def test_invalid_token_no_username(client: AsyncClient, time_in_future: dt.datetime) -> None:
    token = jwt.encode({"exp": time_in_future}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    response = await client.get(
        "/api/notes/my/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == fastapi.status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == UserErrorMessages.invalid_token


async def test_invalid_token_expired(user_client: AsyncClient, time_in_past: dt.datetime) -> None:
    token = jwt.encode(
        {"sub": user_client.user.login, "exp": time_in_past}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    response = await user_client.get(
        "/api/notes/my/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == fastapi.status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == UserErrorMessages.invalid_token
