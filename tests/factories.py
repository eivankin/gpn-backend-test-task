from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app import models


class NoteModelFactory(SQLAlchemyFactory[models.Note]):
    __set_association_proxy__ = False
    __set_relationships__ = False
    __check_model__ = False
    id = None
