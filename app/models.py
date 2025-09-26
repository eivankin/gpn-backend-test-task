import typing

import sqlalchemy as sa
from advanced_alchemy.base import BigIntAuditBase, orm_registry
from sqlalchemy import orm

from app.constraints import NotesConstraints as Constraints


METADATA: typing.Final = orm_registry.metadata
orm.DeclarativeBase.metadata = METADATA


class Note(BigIntAuditBase):
    __tablename__ = "notes"

    title: orm.Mapped[str] = orm.mapped_column(
        sa.String(length=Constraints.max_title_length),
        nullable=False,
    )
    body: orm.Mapped[str | None] = orm.mapped_column(
        sa.String(length=Constraints.max_body_length),
        nullable=False,
    )
