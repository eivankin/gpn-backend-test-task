import sqlalchemy as sa
from advanced_alchemy.base import BigIntAuditBase
from advanced_alchemy.types import PasswordHash
from advanced_alchemy.types.password_hash.passlib import PasslibHasher
from passlib.context import CryptContext
from sqlalchemy import orm

from app.constraints import UsersConstraints as Constraints


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class User(BigIntAuditBase):
    __tablename__ = "users"

    login: orm.Mapped[str] = orm.mapped_column(
        sa.String(length=Constraints.max_login_length),
        nullable=False,
        unique=True,
        index=True,
    )
    password: orm.Mapped[str] = orm.mapped_column(PasswordHash(backend=PasslibHasher(pwd_context)), nullable=False)
    is_admin: orm.Mapped[bool] = orm.mapped_column(
        sa.Boolean(),
        nullable=False,
        default=False,
    )
