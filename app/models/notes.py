import sqlalchemy as sa
from advanced_alchemy.base import BigIntAuditBase
from sqlalchemy import orm

from app.constraints import NotesConstraints as Constraints


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
    author_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_deleted: orm.Mapped[bool] = orm.mapped_column(
        sa.Boolean(),
        nullable=False,
        default=False,
    )
