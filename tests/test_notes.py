from enum import StrEnum

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.error_messages import NotesErrorMessages
from tests import factories
from tests.utils import get_user


class InputExamples(StrEnum):
    null = "null"

    normal_title = "normal note title"
    long_title = "long title"

    normal_body = "normal note body"
    long_body = "long body"

    def get_actual_value(self) -> str | None:
        match self:
            case InputExamples.null:
                return None
            case InputExamples.long_title:
                return "a" * 257
            case InputExamples.long_body:
                return "a" * 65537
            case _:
                return str(self)


async def test_get_notes_empty(user_client: AsyncClient) -> None:
    response = await user_client.get(
        "/api/notes/my/",
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["items"]) == 0


async def test_get_note_does_not_exist(user_client: AsyncClient) -> None:
    response = await user_client.get(
        "/api/notes/0/",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == NotesErrorMessages.note_not_found


async def test_get_notes(user_client: AsyncClient, db_session: AsyncSession) -> None:
    factories.NoteFactory.__async_session__ = db_session
    note = await factories.NoteFactory.create_async(author_id=user_client.user.id)

    response = await user_client.get(
        "/api/notes/my/",
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) == 1
    for k, v in data["items"][0].items():
        assert v == getattr(note, k)


async def test_get_notes_from_other_user(user_client: AsyncClient, db_session: AsyncSession) -> None:
    second_user = await get_user(db_session)

    factories.NoteFactory.__async_session__ = db_session
    await factories.NoteFactory.create_async(author_id=second_user.id)

    response = await user_client.get(
        "/api/notes/my/",
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) == 0


async def test_get_one_note(user_client: AsyncClient, db_session: AsyncSession) -> None:
    factories.NoteFactory.__async_session__ = db_session
    note = await factories.NoteFactory.create_async(author_id=user_client.user.id)

    response = await user_client.get(
        f"/api/notes/{note.id}/",
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    for k, v in data.items():
        assert v == getattr(note, k)


async def test_get_one_note_forbidden(user_client: AsyncClient, db_session: AsyncSession) -> None:
    second_user = await get_user(db_session)
    factories.NoteFactory.__async_session__ = db_session
    note = await factories.NoteFactory.create_async(author_id=second_user.id)

    response = await user_client.get(
        f"/api/notes/{note.id}/",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["detail"] == NotesErrorMessages.access_denied_only_owner


@pytest.mark.parametrize(
    ("title", "body", "status_code"),
    [
        (InputExamples.null, InputExamples.null, status.HTTP_422_UNPROCESSABLE_CONTENT),
        (InputExamples.normal_title, InputExamples.null, status.HTTP_422_UNPROCESSABLE_CONTENT),
        (InputExamples.null, InputExamples.normal_body, status.HTTP_422_UNPROCESSABLE_CONTENT),
        (InputExamples.long_title, InputExamples.normal_body, status.HTTP_422_UNPROCESSABLE_CONTENT),
        (InputExamples.normal_title, InputExamples.long_body, status.HTTP_422_UNPROCESSABLE_CONTENT),
        (InputExamples.normal_title, InputExamples.normal_body, status.HTTP_200_OK),
    ],
)
async def test_post_notes(
    user_client: AsyncClient, title: InputExamples, body: InputExamples, status_code: int
) -> None:
    # create note
    response = await user_client.post(
        "/api/notes/",
        json={
            "title": title.get_actual_value(),
            "body": body.get_actual_value(),
        },
    )
    assert response.status_code == status_code

    # get item
    if status_code == status.HTTP_200_OK:
        item_id = response.json()["id"]
        response = await user_client.get(
            f"/api/notes/{item_id}/",
        )
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert item_id == result["id"]
        assert title == result["title"]
        assert body == result["body"]
        assert user_client.user.id == result["author_id"]


async def test_put_notes_not_exist(user_client: AsyncClient) -> None:
    response = await user_client.put(
        "/api/notes/999/",
        json={"title": "some", "body": "once told me"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    ("title", "body", "status_code"),
    [
        (InputExamples.null, InputExamples.null, status.HTTP_422_UNPROCESSABLE_CONTENT),
        (InputExamples.normal_title, InputExamples.null, status.HTTP_422_UNPROCESSABLE_CONTENT),
        (InputExamples.null, InputExamples.normal_body, status.HTTP_422_UNPROCESSABLE_CONTENT),
        (InputExamples.long_title, InputExamples.normal_body, status.HTTP_422_UNPROCESSABLE_CONTENT),
        (InputExamples.normal_title, InputExamples.long_body, status.HTTP_422_UNPROCESSABLE_CONTENT),
        (InputExamples.normal_title, InputExamples.normal_body, status.HTTP_200_OK),
    ],
)
async def test_put_notes(
    user_client: AsyncClient,
    title: InputExamples,
    body: InputExamples,
    db_session: AsyncSession,
    status_code: int,
) -> None:
    factories.NoteFactory.__async_session__ = db_session
    note = await factories.NoteFactory.create_async(author_id=user_client.user.id)

    # update note
    response = await user_client.put(
        f"/api/notes/{note.id}/",
        json={"title": title.get_actual_value(), "body": body.get_actual_value()},
    )
    assert response.status_code == status_code

    # get item
    item_id = response.json()["id"] if status_code == status.HTTP_200_OK else note.id
    response = await user_client.get(
        f"/api/notes/{item_id}/",
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()

    if status_code == status.HTTP_200_OK:
        assert title == result["title"]
        assert body == result["body"]
    else:
        assert title != result["title"]
        assert body != result["body"]


async def test_put_notes_forbidden(user_client: AsyncClient, db_session: AsyncSession) -> None:
    second_user = await get_user(db_session)
    factories.NoteFactory.__async_session__ = db_session
    note = await factories.NoteFactory.create_async(author_id=second_user.id)

    response = await user_client.put(
        f"/api/notes/{note.id}/",
        json={"title": "some", "body": "once told me"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["detail"] == NotesErrorMessages.access_denied_only_owner


async def test_delete_note(user_client: AsyncClient, db_session: AsyncSession) -> None:
    factories.NoteFactory.__async_session__ = db_session
    note = await factories.NoteFactory.create_async(author_id=user_client.user.id)

    # delete note
    response = await user_client.delete(
        f"/api/notes/{note.id}/",
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # get item
    response = await user_client.get(
        f"/api/notes/{note.id}/",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_note_does_not_exist(user_client: AsyncClient) -> None:
    response = await user_client.delete(
        "/api/notes/999/",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_note_forbidden(user_client: AsyncClient, db_session: AsyncSession) -> None:
    second_user = await get_user(db_session)
    factories.NoteFactory.__async_session__ = db_session
    note = await factories.NoteFactory.create_async(author_id=second_user.id)

    response = await user_client.delete(
        f"/api/notes/{note.id}/",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["detail"] == NotesErrorMessages.access_denied_only_owner


# TODO: test admin methods
