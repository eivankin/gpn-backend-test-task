from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from polyfactory.pytest_plugin import register_fixture

from app import models


@register_fixture
class NoteFactory(SQLAlchemyFactory[models.Note]):
    __set_association_proxy__ = False
    __set_relationships__ = False
    __check_model__ = False
    id = None
    is_deleted = False


@register_fixture
class UserFactory(SQLAlchemyFactory[models.User]):
    __set_association_proxy__ = False
    __set_relationships__ = False
    __check_model__ = False
    id = None
    password = "password"
