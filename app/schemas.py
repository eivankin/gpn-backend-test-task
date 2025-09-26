from typing import Annotated

import pydantic
from pydantic import BaseModel, PositiveInt, StringConstraints

from app.constraints import NotesConstraints as Constraints


class Base(BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)


class NoteBase(Base):
    title: Annotated[str, StringConstraints(max_length=Constraints.max_title_length)]
    body: Annotated[str, StringConstraints(max_length=Constraints.max_body_length)]


class NoteCreate(NoteBase):
    pass


class Note(NoteBase):
    id: PositiveInt
