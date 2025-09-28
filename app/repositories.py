from typing import TYPE_CHECKING

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
from sqlalchemy import true
from sqlalchemy.sql import not_

from app import models
from app.exceptions import AccessDeniedError


if TYPE_CHECKING:
    from advanced_alchemy.service.typing import ModelDictT


class NotesRepository(SQLAlchemyAsyncRepository[models.Note]):
    model_type = models.Note


class NotesService(SQLAlchemyAsyncRepositoryService[models.Note]):
    not_deleted_filter = not_(models.Note.is_deleted)
    repository_type = NotesRepository

    @staticmethod
    def _check_is_owner(note: models.Note, user: models.User) -> None:
        if note.author_id != user.id:
            raise AccessDeniedError

    @staticmethod
    def _check_is_admin_or_owner(note: models.Note, user: models.User) -> None:
        if not user.is_admin and note.author_id != user.id:
            raise AccessDeniedError

    async def create_with_author(self, data: "ModelDictT[models.Note]", author: models.User, **kwargs) -> models.Note:
        data = await self.to_model(data, "update")
        data.author_id = author.id
        return await super().create(data=data, **kwargs)

    async def soft_delete(self, item_id: int, user: models.User, **kwargs) -> models.Note:
        instance = await self.get_one(models.Note.id == item_id, self.not_deleted_filter)
        self._check_is_owner(instance, user)
        instance.is_deleted = True
        return await super().update(data=instance, item_id=item_id, **kwargs)

    async def update_with_access_check(
        self,
        data: "ModelDictT[models.Note]",
        item_id: int,
        user: models.User,
        **kwargs,
    ) -> models.Note:
        instance = await self.get_one(models.Note.id == item_id, self.not_deleted_filter)
        self._check_is_owner(instance, user)
        return await super().update(data=data, item_id=item_id, **kwargs)

    async def get_one_with_access_check(self, *filters, user: models.User) -> models.Note:
        instance = await self.get_one(*filters, self.not_deleted_filter)
        self._check_is_admin_or_owner(instance, user)
        return instance

    async def restore(self, item_id: int, **kwargs) -> models.Note:
        instance = await self.get_one(models.Note.id == item_id, models.Note.is_deleted == true())
        instance.is_deleted = False
        return await super().update(data=instance, item_id=item_id, **kwargs)


class UsersRepository(SQLAlchemyAsyncRepository[models.User]):
    model_type = models.User


class UsersService(SQLAlchemyAsyncRepositoryService[models.User]):
    repository_type = UsersRepository
