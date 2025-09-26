from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from app import models


class NotesRepository(SQLAlchemyAsyncRepository[models.Note]):
    model_type = models.Note


class NotesService(SQLAlchemyAsyncRepositoryService[models.Note]):
    repository_type = NotesRepository
