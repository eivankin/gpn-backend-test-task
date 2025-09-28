from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt import InvalidTokenError
from modern_di_fastapi import FromDI

from app import ioc, models
from app.error_messages import UserErrorMessages as Errors
from app.repositories import UsersService
from app.schemas.auth import TokenData
from app.settings import settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/token/")


async def authenticate_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    users_service: UsersService = FromDI(ioc.Dependencies.users_service),
) -> models.User:
    username = form_data.username
    password = form_data.password
    user = await users_service.get_one_or_none(models.User.login == username)
    if not user or not user.password.verify(password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail=Errors.wrong_login_pass, headers={"WWW-Authenticate": "Bearer"}
        )
    return user


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], users_service: UsersService = FromDI(ioc.Dependencies.users_service)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=Errors.invalid_token,
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception from None
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception from None
    user = await users_service.get_one_or_none(models.User.login == token_data.username)
    if user is None:
        raise credentials_exception
    return user
