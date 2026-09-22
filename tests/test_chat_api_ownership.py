from __future__ import annotations

from uuid import UUID

import pytest
from fastapi import HTTPException

import services.api.main as api
from nanexus.auth import Principal
from nanexus.chat_v1 import create_chat_job
from nanexus.models import ChatJob, ChatMessage, Conversation
from nanexus.schemas import ChatV1Request


class FakeChatDB:
    def __init__(self) -> None:
        self.items: dict[tuple[type[object], object], object] = {}
        self.pending: list[object] = []

    def add(self, item: object) -> None:
        self.pending.append(item)

    def flush(self) -> None:
        for item in self.pending:
            if isinstance(item, Conversation) and item.id is None:
                item.id = 7
            if isinstance(item, (ChatMessage, ChatJob)) and item.id is None:
                item.id = UUID(
                    f"00000000-0000-0000-0000-{len(self.items) + 1:012d}"
                )
            self.items[(type(item), item.id)] = item

    def commit(self) -> None:
        self.flush()

    def refresh(self, _item: object) -> None:
        pass

    def get(self, model: type[object], identifier: object) -> object | None:
        return self.items.get((model, identifier))

    def scalars(self, _query: object) -> EmptyScalars:
        return EmptyScalars()


class EmptyScalars:
    def all(self) -> list[object]:
        return []


class FakeQueue:
    def enqueue_chat(self, _job: object) -> None:
        pass


@pytest.fixture
def chat_db(monkeypatch: pytest.MonkeyPatch) -> FakeChatDB:
    db = FakeChatDB()
    monkeypatch.setattr(api.settings, "auth_mode", "development")
    monkeypatch.setattr(api, "AIQueue", FakeQueue)
    return db


def principal(owner_id: str) -> Principal:
    return Principal(owner_id=owner_id, role="user", sites=frozenset({"*"}))


def create_job(db: FakeChatDB, owner_id: str) -> ChatJob:
    return create_chat_job(
        db,
        owner_id=owner_id,
        question="What happened?",
        conversation_id=None,
        camera=None,
        site_id="default",
        timezone="UTC",
    )


def test_development_chat_job_defaults_reads_to_principal_owner(
    chat_db: FakeChatDB,
) -> None:
    local_web = principal("local-web")
    created = api.create_chat_job_v1(
        ChatV1Request(message="What happened?"), chat_db, local_web
    )
    fetched = api.get_chat_job_v1(created.id, None, chat_db, local_web)
    assert fetched.id == created.id


def test_development_conversation_defaults_reads_to_principal_owner(
    chat_db: FakeChatDB,
) -> None:
    conversation = Conversation(id=11, user_id="local-web", title="Development")
    chat_db.items[(Conversation, conversation.id)] = conversation
    response = api.get_conversation_v1(
        conversation.id, None, chat_db, principal("local-web")
    )
    assert response.owner_id == "local-web"


def test_explicit_development_owner_remains_supported(chat_db: FakeChatDB) -> None:
    job = create_job(chat_db, "explicit-owner")
    response = api.get_chat_job_v1(
        job.id, "explicit-owner", chat_db, principal("local-web")
    )
    assert response.id == job.id


def test_mismatched_development_owner_remains_isolated(chat_db: FakeChatDB) -> None:
    job = create_job(chat_db, "other-owner")
    with pytest.raises(HTTPException) as denied:
        api.get_chat_job_v1(job.id, None, chat_db, principal("local-web"))
    assert denied.value.status_code == 404


def test_static_authentication_ignores_query_owner(
    chat_db: FakeChatDB, monkeypatch: pytest.MonkeyPatch
) -> None:
    alice_job = create_job(chat_db, "alice")
    bob_job = create_job(chat_db, "bob")
    monkeypatch.setattr(api.settings, "auth_mode", "static")
    alice = principal("alice")
    own_response = api.get_chat_job_v1(alice_job.id, "bob", chat_db, alice)
    with pytest.raises(HTTPException) as denied:
        api.get_chat_job_v1(bob_job.id, "bob", chat_db, alice)
    assert own_response.id == alice_job.id
    assert denied.value.status_code == 404
