"""Unit tests for moderation alarm repository persistence helpers."""
import uuid
from unittest.mock import AsyncMock, Mock

import pytest

from src.models.flagged_event_model import Alarm
from src.repo.flagged_event_repo import FlaggedEventRepository


@pytest.mark.asyncio
async def test_log_event_creates_alarm_with_uuid_fields() -> None:
    """Repository should cast string identifiers to UUIDs before persisting."""
    session = Mock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    repo = FlaggedEventRepository(session)
    user_id = str(uuid.uuid4())
    conversation_id = str(uuid.uuid4())

    event = await repo.log_event(
        user_id=user_id,
        conversation_id=conversation_id,
        message_content="harmful content",
        filter_type="keyword",
        provider="groq",
    )

    persisted_event = session.add.call_args.args[0]

    assert isinstance(event, Alarm)
    assert persisted_event is event
    assert event.user_id == uuid.UUID(user_id)
    assert event.conversation_id == uuid.UUID(conversation_id)
    assert event.message_content == "harmful content"
    assert event.filter_type == "keyword"
    assert event.provider == "groq"
    session.commit.assert_awaited_once_with()
    session.refresh.assert_awaited_once_with(event)


@pytest.mark.asyncio
async def test_get_all_events_returns_scalar_results_in_created_order() -> None:
    """Repository should return the scalar alarm rows from the ordered select statement."""
    session = Mock()
    expected_events = [
        Alarm(
            user_id=uuid.uuid4(),
            conversation_id=uuid.uuid4(),
            message_content="first",
            filter_type="keyword",
            provider="groq",
        ),
        Alarm(
            user_id=uuid.uuid4(),
            conversation_id=uuid.uuid4(),
            message_content="second",
            filter_type="provider",
            provider="deepseek",
        ),
    ]

    scalar_result = Mock()
    scalar_result.all.return_value = expected_events

    execute_result = Mock()
    execute_result.scalars.return_value = scalar_result

    session.execute = AsyncMock(return_value=execute_result)

    repo = FlaggedEventRepository(session)
    events = await repo.get_all_events()

    assert events == expected_events
    session.execute.assert_awaited_once()
    statement = session.execute.await_args.args[0]
    assert "FROM alarm" in str(statement)
    assert "ORDER BY alarm.created_at" in str(statement)
