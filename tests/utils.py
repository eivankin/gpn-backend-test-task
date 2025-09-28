import fastapi
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from tests import factories


async def get_user(db_session: AsyncSession, is_admin: bool = False) -> models.User:
    factories.UserFactory.__async_session__ = db_session
    return await factories.UserFactory.create_async(is_admin=is_admin)


async def get_token(client: AsyncClient, user: models.User) -> str:
    response = await client.post("/api/users/token/", data={"username": user.login, "password": "password"})
    assert response.status_code == fastapi.status.HTTP_200_OK
    return response.json()["access_token"]


async def user_auth(client: AsyncClient, db_session: AsyncSession, is_admin: bool = False) -> tuple[str, models.User]:
    user = await get_user(db_session, is_admin)
    token = await get_token(client, user)
    return token, user
