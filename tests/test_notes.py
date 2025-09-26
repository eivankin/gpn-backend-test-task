import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.error_messages import NotesErrorMessages
from tests import factories


LONG_TITLE = "a" * 257
LONG_BODY = "a" * 65537


async def test_get_notes_empty(client: AsyncClient) -> None:
    response = await client.get("/api/notes/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["items"]) == 0


async def test_get_note_does_not_exist(client: AsyncClient) -> None:
    response = await client.get("/api/notes/0/")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == NotesErrorMessages.note_not_found


async def test_get_notes(client: AsyncClient, db_session: AsyncSession) -> None:
    factories.NoteModelFactory.__async_session__ = db_session
    note = await factories.NoteModelFactory.create_async()

    response = await client.get("/api/notes/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) == 1
    for k, v in data["items"][0].items():
        assert v == getattr(note, k)


async def test_get_one_note(client: AsyncClient, db_session: AsyncSession) -> None:
    factories.NoteModelFactory.__async_session__ = db_session
    note = await factories.NoteModelFactory.create_async()

    response = await client.get(f"/api/notes/{note.id}/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    for k, v in data.items():
        assert v == getattr(note, k)


@pytest.mark.parametrize(
    ("title", "body", "status_code"),
    [
        (None, None, status.HTTP_422_UNPROCESSABLE_CONTENT),
        ("test note", None, status.HTTP_422_UNPROCESSABLE_CONTENT),
        (None, "test note body", status.HTTP_422_UNPROCESSABLE_CONTENT),
        (LONG_TITLE, "test note body", status.HTTP_422_UNPROCESSABLE_CONTENT),
        ("test note", LONG_BODY, status.HTTP_422_UNPROCESSABLE_CONTENT),
        ("test note", "test note body", status.HTTP_200_OK),
    ],
)
async def test_post_notes(
    client: AsyncClient,
    title: str,
    body: str,
    status_code: int,
) -> None:
    # create note
    response = await client.post(
        "/api/notes/",
        json={
            "title": title,
            "body": body,
        },
    )
    assert response.status_code == status_code

    # get item
    if status_code == status.HTTP_200_OK:
        item_id = response.json()["id"]
        response = await client.get(f"/api/notes/{item_id}/")
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert item_id == result["id"]
        assert title == result["title"]
        assert body == result["body"]


async def test_put_notes_wrong_body(client: AsyncClient, db_session: AsyncSession) -> None:
    factories.NoteModelFactory.__async_session__ = db_session
    note = await factories.NoteModelFactory.create_async()

    # update note
    response = await client.put(
        f"/api/notes/{note.id}/",
        json={"title": None, "body": None},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_put_notes_not_exist(client: AsyncClient) -> None:
    response = await client.put(
        "/api/notes/999/",
        json={"title": "some", "body": "once told me"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    ("title", "body", "status_code"),
    [
        ("test note updated", None, status.HTTP_422_UNPROCESSABLE_CONTENT),
        (None, "test note body updated", status.HTTP_422_UNPROCESSABLE_CONTENT),
        (LONG_TITLE, "test note body updated", status.HTTP_422_UNPROCESSABLE_CONTENT),
        ("test note updated", LONG_BODY, status.HTTP_422_UNPROCESSABLE_CONTENT),
        ("test note updated", "test note body updated", status.HTTP_200_OK),
    ],
)
async def test_put_notes(
    client: AsyncClient,
    title: str,
    body: str,
    db_session: AsyncSession,
    status_code: int,
) -> None:
    factories.NoteModelFactory.__async_session__ = db_session
    note = await factories.NoteModelFactory.create_async()

    # update note
    response = await client.put(
        f"/api/notes/{note.id}/",
        json={"title": title, "body": body},
    )
    assert response.status_code == status_code

    # get item
    item_id = response.json()["id"] if status_code == status.HTTP_200_OK else note.id
    response = await client.get(f"/api/notes/{item_id}/")
    assert response.status_code == status.HTTP_200_OK
    result = response.json()

    if status_code == status.HTTP_200_OK:
        assert title == result["title"]
        assert body == result["body"]
    else:
        assert title != result["title"]
        assert body != result["body"]


async def test_delete_note(client: AsyncClient, db_session: AsyncSession) -> None:
    factories.NoteModelFactory.__async_session__ = db_session
    note = await factories.NoteModelFactory.create_async()

    # delete note
    response = await client.delete(f"/api/notes/{note.id}/")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # get item
    response = await client.get(f"/api/notes/{note.id}/")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_note_does_not_exist(client: AsyncClient) -> None:
    response = await client.delete("/api/notes/999/")
    assert response.status_code == status.HTTP_404_NOT_FOUND
