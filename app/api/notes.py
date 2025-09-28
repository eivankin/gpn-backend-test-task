import sys
import typing

import fastapi
from advanced_alchemy.exceptions import NotFoundError
from advanced_alchemy.extensions.fastapi import filters as aa_filters
from advanced_alchemy.extensions.fastapi.providers import provide_filters
from advanced_alchemy.service import OffsetPagination
from fastapi import Depends, status
from loguru import logger
from modern_di_fastapi import FromDI

from app import ioc, models, schemas
from app.auth import get_current_user
from app.error_messages import NotesErrorMessages as Errors
from app.exceptions import AccessDeniedError
from app.repositories import NotesService
from app.settings import settings


ROUTER: typing.Final = fastapi.APIRouter(prefix="/notes")

logger.remove()
logger.add(sys.stderr, level=settings.log_level.upper(), filter=lambda record: record["name"] != "app.api.notes")
logger.add(
    settings.actions_log_file,
    level=settings.log_level.upper(),
    filter="app.api.notes",
    format="{time} | {level: <8} | {name}:{function}:{line} - User #{extra[user_id]} "
    "with role '{extra[user_role]}' {message}",
)


@ROUTER.get("/my/", response_model=OffsetPagination[schemas.Note])
async def list_my_notes(
    filters: typing.Annotated[
        list[aa_filters.FilterTypes],
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
    with logger.contextualize(user_id=user.id, user_role=user.verbose_role):
        results, total = await notes_service.list_and_count(
            models.Note.author_id == user.id,
            notes_service.not_deleted_filter,
            *filters,
        )
        logger.info("successfully listed their notes")
        return notes_service.to_schema(results, total, filters=filters, schema_type=schemas.Note)


@ROUTER.get("/", response_model=OffsetPagination[schemas.NoteAdmin])
async def list_notes(
    filters: typing.Annotated[
        list[aa_filters.FilterTypes],
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
    author_id: int | None = None,
) -> OffsetPagination[schemas.Note]:
    with logger.contextualize(user_id=user.id, user_role=user.verbose_role):
        if not user.is_admin:
            logger.warning("tried to access admin-only list of notes")
            raise fastapi.HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=Errors.access_denied_only_admin
            ) from None
        extra_info = ""
        if author_id is not None:
            filters.append(models.Note.author_id == author_id)
            extra_info = f" for author with ID: {author_id}"
        results, total = await notes_service.list_and_count(*filters)
        logger.info("successfully listed notes" + extra_info)
        return notes_service.to_schema(results, total, filters=filters, schema_type=schemas.NoteAdmin)


@ROUTER.get("/{note_id}/")
async def get_note(
    note_id: int,
    notes_service: NotesService = FromDI(ioc.Dependencies.notes_service),
    user: models.User = Depends(get_current_user),
) -> schemas.Note:
    with logger.contextualize(user_id=user.id, user_role=user.verbose_role):
        try:
            instance = await notes_service.get_one_with_access_check(models.Note.id == note_id, user=user)
            logger.info(f"successfully accessed note #{note_id}")
        except AccessDeniedError:
            logger.warning(f"tried to access note #{note_id} of another user")
            raise fastapi.HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=Errors.access_denied_only_owner
            ) from None
        except NotFoundError:
            logger.warning(f"tried to access non-existent note #{note_id}")
            raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=Errors.note_not_found) from None

        return typing.cast("schemas.Note", instance)


@ROUTER.put("/{note_id}/")
async def update_note(
    note_id: int,
    data: schemas.NoteCreate,
    notes_service: NotesService = FromDI(ioc.Dependencies.notes_service),
    user: models.User = Depends(get_current_user),
) -> schemas.Note:
    with logger.contextualize(user_id=user.id, user_role=user.verbose_role):
        try:
            instance = await notes_service.update_with_access_check(data=data.model_dump(), item_id=note_id, user=user)
            logger.info(f"successfully updated note #{note_id}")
        except AccessDeniedError:
            logger.warning(f"tried to update note #{note_id} of another user")
            raise fastapi.HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=Errors.access_denied_only_owner
            ) from None
        except NotFoundError:
            logger.warning(f"tried to update non-existent note #{note_id}")
            raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=Errors.note_not_found) from None

    return typing.cast("schemas.Note", instance)


@ROUTER.delete("/{note_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: int,
    notes_service: NotesService = FromDI(ioc.Dependencies.notes_service),
    user: models.User = Depends(get_current_user),
) -> None:
    with logger.contextualize(user_id=user.id, user_role=user.verbose_role):
        try:
            await notes_service.soft_delete(item_id=note_id, user=user)
            logger.info(f"successfully deleted note #{note_id}")
        except AccessDeniedError:
            logger.warning(f"tried to delete note #{note_id} of another user")
            raise fastapi.HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=Errors.access_denied_only_owner
            ) from None
        except NotFoundError:
            logger.warning(f"tried to delete non-existent note #{note_id}")
            raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=Errors.note_not_found) from None


@ROUTER.post("/", status_code=status.HTTP_201_CREATED)
async def create_note(
    data: schemas.NoteCreate,
    notes_service: NotesService = FromDI(ioc.Dependencies.notes_service),
    user: models.User = Depends(get_current_user),
) -> schemas.Note:
    with logger.contextualize(user_id=user.id, user_role=user.verbose_role):
        instance = await notes_service.create_with_author(data.model_dump(), author=user)
        logger.info(f"successfully created note #{instance.id}")
        return typing.cast("schemas.Note", instance)


@ROUTER.post("/{note_id}/restore/")
async def restore_note(
    note_id: int,
    notes_service: NotesService = FromDI(ioc.Dependencies.notes_service),
    user: models.User = Depends(get_current_user),
) -> schemas.Note:
    with logger.contextualize(user_id=user.id, user_role=user.verbose_role):
        if not user.is_admin:
            logger.warning(f"tried to restore note #{note_id}")
            raise fastapi.HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=Errors.access_denied_only_admin)
        try:
            instance = await notes_service.restore(item_id=note_id)
        except NotFoundError:
            logger.warning(f"tried to restore non-existent note #{note_id}")
            raise fastapi.HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=Errors.note_not_found) from None
        logger.info(f"successfully restored note #{instance.id}")
        return typing.cast("schemas.Note", instance)
