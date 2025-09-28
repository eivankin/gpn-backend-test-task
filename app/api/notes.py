import typing

import fastapi
from advanced_alchemy.exceptions import NotFoundError
from advanced_alchemy.extensions.fastapi import filters
from advanced_alchemy.extensions.fastapi.providers import provide_filters
from advanced_alchemy.service import OffsetPagination
from fastapi import Depends, status
from modern_di_fastapi import FromDI

from app import ioc, models, schemas
from app.auth import get_current_user
from app.error_messages import NotesErrorMessages as Errors
from app.exceptions import AccessDeniedError
from app.repositories import NotesService


# TODO: separate logger for user actions

ROUTER: typing.Final = fastapi.APIRouter(prefix="/notes")


@ROUTER.get("/my/", response_model=OffsetPagination[schemas.Note])
async def list_my_notes(
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
    user: models.User = Depends(get_current_user),
) -> OffsetPagination[schemas.Note]:
    results, total = await notes_service.list_and_count(
        models.Note.author_id == user.id,
        notes_service.not_deleted_filter,
        *filters,
    )
    return notes_service.to_schema(results, total, filters=filters, schema_type=schemas.Note)


@ROUTER.get("/{note_id}/")
async def get_note(
    note_id: int,
    notes_service: NotesService = FromDI(ioc.Dependencies.notes_service),
    user: models.User = Depends(get_current_user),
) -> schemas.Note:
    try:
        instance = await notes_service.get_one_with_access_check(models.Note.id == note_id, user=user)
    except AccessDeniedError:
        raise fastapi.HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=Errors.access_denied_only_owner
        ) from None
    except NotFoundError:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=Errors.note_not_found) from None

    return typing.cast("schemas.Note", instance)


@ROUTER.put("/{note_id}/")
async def update_note(
    note_id: int,
    data: schemas.NoteCreate,
    notes_service: NotesService = FromDI(ioc.Dependencies.notes_service),
    user: models.User = Depends(get_current_user),
) -> schemas.Note:
    try:
        instance = await notes_service.update_with_access_check(data=data.model_dump(), item_id=note_id, user=user)
    except AccessDeniedError:
        raise fastapi.HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=Errors.access_denied_only_owner
        ) from None
    except NotFoundError:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=Errors.note_not_found) from None

    return typing.cast("schemas.Note", instance)


@ROUTER.delete("/{note_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: int,
    notes_service: NotesService = FromDI(ioc.Dependencies.notes_service),
    user: models.User = Depends(get_current_user),
) -> None:
    try:
        await notes_service.soft_delete(item_id=note_id, user=user)
    except AccessDeniedError:
        raise fastapi.HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=Errors.access_denied_only_owner
        ) from None
    except NotFoundError:
        raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=Errors.note_not_found) from None


@ROUTER.post("/")
async def create_note(
    data: schemas.NoteCreate,
    notes_service: NotesService = FromDI(ioc.Dependencies.notes_service),
    user: models.User = Depends(get_current_user),
) -> schemas.Note:
    instance = await notes_service.create_with_author(data.model_dump(), author=user)
    return typing.cast("schemas.Note", instance)


# TODO: handle restore deleted note by admin
