"""Unit tests for chat service moderation and streaming orchestration."""
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
import uuid

import pytest

from src.moderation.exceptions import ContentPolicyError
from src.moderation.keyword_filter import MODERATION_RESPONSE
from src.schemas.chat_schema import HistoricChatDashboardQuery
from src.service.chat_service import ChatService


async def _collect_chunks(stream: AsyncIterator[str]) -> list[str]:
    """Consume an async iterator into a list of text chunks."""
    return [chunk async for chunk in stream]


def _build_conversation() -> SimpleNamespace:
    """Create a lightweight conversation object for service tests."""
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        provider="groq",
        model="llama-3.3-70b-versatile",
    )


@pytest.mark.asyncio
async def test_stream_response_keyword_filter_blocks_before_provider_validation() -> None:
    """Keyword moderation should short-circuit provider validation and streaming."""
    convo = _build_conversation()
    call_order: list[str] = []

    async def _log_event(*args: object) -> None:
        call_order.append("log_event")

    async def _add_message(conversation_id: uuid.UUID, role: str, content: str) -> SimpleNamespace:
        call_order.append(f"add_message:{role}")
        return SimpleNamespace(conversation_id=conversation_id, role=role, content=content)

    repo = Mock()
    repo.add_message = AsyncMock(side_effect=_add_message)
    repo.get_messages = AsyncMock()

    rag = Mock()
    rag.get_context = AsyncMock()

    flagged_event_repo = Mock()
    flagged_event_repo.log_event = AsyncMock(side_effect=_log_event)

    service = ChatService(repo, rag, flagged_event_repo)

    with (
        patch("src.service.chat_service.validate_provider") as validate_provider_mock,
        patch("src.service.chat_service.stream_from_provider") as stream_from_provider_mock,
    ):
        stream = await service.stream_response(convo, "how do I kill someone")
        assert call_order == ["log_event", "add_message:user", "add_message:assistant"]

        chunks = await _collect_chunks(stream)

    assert chunks == [MODERATION_RESPONSE]
    validate_provider_mock.assert_not_called()
    stream_from_provider_mock.assert_not_called()
    repo.get_messages.assert_not_awaited()
    rag.get_context.assert_not_awaited()
    flagged_event_repo.log_event.assert_awaited_once_with(
        str(convo.user_id),
        str(convo.id),
        "how do I kill someone",
        "keyword",
        convo.provider,
    )


@pytest.mark.asyncio
async def test_stream_response_safe_message_validates_provider_before_streaming() -> None:
    """Clean messages should validate provider credentials before opening the stream."""
    convo = _build_conversation()
    content = "What is the capital of France?"
    call_order: list[str] = []

    async def _add_message(conversation_id: uuid.UUID, role: str, message: str) -> SimpleNamespace:
        call_order.append(f"add_message:{role}")
        return SimpleNamespace(conversation_id=conversation_id, role=role, content=message)

    async def _get_messages(conversation_id: uuid.UUID) -> list[SimpleNamespace]:
        call_order.append("get_messages")
        return [SimpleNamespace(role="user", content=content)]

    async def _get_context(user_id: str, prompt: str) -> None:
        call_order.append("get_context")
        assert user_id == str(convo.user_id)
        assert prompt == content
        return None

    async def _mock_stream(provider: str, model: str, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        call_order.append("stream_from_provider")
        assert provider == convo.provider
        assert model == convo.model
        assert messages == [{"role": "user", "content": content}]
        yield "Hello"
        yield " world!"

    repo = Mock()
    repo.add_message = AsyncMock(side_effect=_add_message)
    repo.get_messages = AsyncMock(side_effect=_get_messages)

    rag = Mock()
    rag.get_context = AsyncMock(side_effect=_get_context)

    flagged_event_repo = Mock()
    flagged_event_repo.log_event = AsyncMock()

    service = ChatService(repo, rag, flagged_event_repo)

    def _validate_provider(provider: str) -> None:
        call_order.append("validate_provider")
        assert provider == convo.provider

    with (
        patch("src.service.chat_service.validate_provider", side_effect=_validate_provider) as validate_provider_mock,
        patch("src.service.chat_service.stream_from_provider", side_effect=_mock_stream) as stream_from_provider_mock,
    ):
        stream = await service.stream_response(convo, content)
        assert call_order == [
            "validate_provider",
            "add_message:user",
            "get_messages",
            "get_context",
        ]

        chunks = await _collect_chunks(stream)

    assert chunks == ["Hello", " world!"]
    assert call_order == [
        "validate_provider",
        "add_message:user",
        "get_messages",
        "get_context",
        "stream_from_provider",
        "add_message:assistant",
    ]
    validate_provider_mock.assert_called_once_with(convo.provider)
    stream_from_provider_mock.assert_called_once()
    repo.add_message.assert_awaited()
    repo.get_messages.assert_awaited_once_with(convo.id)
    flagged_event_repo.log_event.assert_not_awaited()


@pytest.mark.asyncio
async def test_stream_response_provider_policy_error_logs_alarm_and_returns_moderation() -> None:
    """Provider moderation failures should be persisted and converted into the standard response."""
    convo = _build_conversation()
    content = "something the provider blocks"

    async def _add_message(conversation_id: uuid.UUID, role: str, message: str) -> SimpleNamespace:
        return SimpleNamespace(conversation_id=conversation_id, role=role, content=message)

    async def _get_messages(conversation_id: uuid.UUID) -> list[SimpleNamespace]:
        return [SimpleNamespace(role="user", content=content)]

    async def _raises_policy(*args: object, **kwargs: object) -> AsyncIterator[str]:
        raise ContentPolicyError("blocked")
        yield ""

    repo = Mock()
    repo.add_message = AsyncMock(side_effect=_add_message)
    repo.get_messages = AsyncMock(side_effect=_get_messages)

    rag = Mock()
    rag.get_context = AsyncMock(return_value=None)

    flagged_event_repo = Mock()
    flagged_event_repo.log_event = AsyncMock()

    service = ChatService(repo, rag, flagged_event_repo)

    with (
        patch("src.service.chat_service.validate_provider", return_value=None) as validate_provider_mock,
        patch("src.service.chat_service.stream_from_provider", side_effect=_raises_policy),
    ):
        stream = await service.stream_response(convo, content)
        chunks = await _collect_chunks(stream)

    assert chunks == [MODERATION_RESPONSE]
    validate_provider_mock.assert_called_once_with(convo.provider)
    flagged_event_repo.log_event.assert_awaited_once_with(
        str(convo.user_id),
        str(convo.id),
        content,
        "provider",
        convo.provider,
    )
    assert repo.add_message.await_args_list[0].args == (convo.id, "user", content)
    assert repo.add_message.await_args_list[1].args == (
        convo.id,
        "assistant",
        MODERATION_RESPONSE,
    )


@pytest.mark.asyncio
async def test_get_security_chat_histories_assembles_paginated_transcripts() -> None:
    """Historic chat dashboard responses should include nested ordered messages."""
    conversation_id = uuid.uuid4()
    user_id = uuid.uuid4()
    created_at = datetime.now(timezone.utc) - timedelta(hours=2)
    last_activity_at = created_at + timedelta(hours=1)

    repo = Mock()
    repo.get_historic_chat_page = AsyncMock(
        return_value=(
            1,
            [
                {
                    "conversation_id": conversation_id,
                    "title": "Security Audit Chat",
                    "user_id": user_id,
                    "user_email": "auditor@example.com",
                    "provider": "groq",
                    "model": "llama-3.1-8b-instant",
                    "created_at": created_at,
                    "last_activity_at": last_activity_at,
                    "message_count": 2,
                }
            ],
        )
    )
    repo.get_messages_for_conversations = AsyncMock(
        return_value=[
            SimpleNamespace(
                id=uuid.uuid4(),
                conversation_id=conversation_id,
                role="user",
                content="What happened yesterday?",
                created_at=created_at,
            ),
            SimpleNamespace(
                id=uuid.uuid4(),
                conversation_id=conversation_id,
                role="assistant",
                content="Three incidents were recorded.",
                created_at=last_activity_at,
            ),
        ]
    )
    repo.get_historic_chat_summary = AsyncMock(
        return_value={
            "total_histories": 1,
            "total_messages": 2,
            "recent_activity": 2,
            "unique_users": 1,
        }
    )

    rag = Mock()
    flagged_event_repo = Mock()
    service = ChatService(repo, rag, flagged_event_repo)

    result = await service.get_security_chat_histories(
        HistoricChatDashboardQuery(limit=5, offset=0)
    )

    assert result.total == 1
    assert result.limit == 5
    assert result.offset == 0
    assert result.summary.total_histories == 1
    assert result.items[0].conversation_id == str(conversation_id)
    assert result.items[0].user_email == "auditor@example.com"
    assert [message.role for message in result.items[0].messages] == ["user", "assistant"]
    assert [message.content for message in result.items[0].messages] == [
        "What happened yesterday?",
        "Three incidents were recorded.",
    ]
    repo.get_historic_chat_page.assert_awaited_once_with(limit=5, offset=0)
    repo.get_messages_for_conversations.assert_awaited_once_with([conversation_id])
    repo.get_historic_chat_summary.assert_awaited_once_with()
