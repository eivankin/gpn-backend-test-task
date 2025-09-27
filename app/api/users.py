import typing

import fastapi
from fastapi import Depends

from app import models
from app.auth import authenticate_user, create_access_token
from app.schemas import Token


ROUTER: typing.Final = fastapi.APIRouter(prefix="/users")


@ROUTER.post("/token")
async def login_for_access_token(user: models.User = Depends(authenticate_user)) -> Token:
    access_token = create_access_token(data={"sub": user.login})
    return Token(access_token=access_token, token_type="bearer")
