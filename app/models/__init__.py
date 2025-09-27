import typing

from advanced_alchemy.base import orm_registry
from sqlalchemy import orm

from app.models.notes import Note
from app.models.users import User


METADATA: typing.Final = orm_registry.metadata
orm.DeclarativeBase.metadata = METADATA


__all__ = [
    "METADATA",
    "Note",
    "User",
]
