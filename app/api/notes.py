import typing

import fastapi
from advanced_alchemy.exceptions import NotFoundError
from advanced_alchemy.extensions.fastapi import filters
from advanced_alchemy.extensions.fastapi.providers import provide_filters
from advanced_alchemy.service import OffsetPagination
from fastapi import Depends
from modern_di_fastapi import FromDI
from starlette import status

from app import ioc, models, schemas
from app.error_messages import NotesErrorMessages as Errors
from app.repositories import NotesService


ROUTER: typing.Final = fastapi.APIRouter(prefix="/notes")


@ROUTER.get("/", response_model=OffsetPagination[schemas.Note])
async def list_notes(
    filters: typing.Annotated[
        list[filters.FilterTypes],
        Depends(
            provide_filters(
                {
                    "pagination_type": "limit_offset",
                }
            )
        ),
    ],
    notes_service: NotesService = FromDI(ioc.Dependencies.notes_service),
) -> OffsetPagination[schemas.Note]:
    results, total = await notes_service.list_and_count(*filters)
    return notes_service.to_schema(results, total, filters=filters, schema_type=schemas.Note)


@ROUTER.get("/{note_id}/")
async def get_note(
    note_id: int,
    notes_service: NotesService = FromDI(ioc.Dependencies.notes_service),
) -> schemas.Note:
    instance = await notes_service.get_one_or_none(
        models.Note.id == note_id,
    )
    if not instance:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=Errors.note_not_found)

    return typing.cast("schemas.Note", instance)


@ROUTER.put("/{note_id}/")
async def update_note(
    note_id: int,
    data: schemas.NoteCreate,
    notes_service: NotesService = FromDI(ioc.Dependencies.notes_service),
) -> schemas.Note:
    try:
        instance = await notes_service.update(data=data.model_dump(), item_id=note_id)
    except NotFoundError:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=Errors.note_not_found) from None

    return typing.cast("schemas.Note", instance)


@ROUTER.delete("/{note_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: int,
    notes_service: NotesService = FromDI(ioc.Dependencies.notes_service),
) -> None:
    try:
        await notes_service.delete(item_id=note_id)
    except NotFoundError:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=Errors.note_not_found) from None


@ROUTER.post("/")
async def create_note(
    data: schemas.NoteCreate,
    notes_service: NotesService = FromDI(ioc.Dependencies.notes_service),
) -> schemas.Note:
    instance = await notes_service.create(data.model_dump())
    return typing.cast("schemas.Note", instance)
