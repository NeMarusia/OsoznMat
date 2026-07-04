from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, inspect

from bot.db import StateStorage, User, database_url, init_database


def test_state_storage_requires_existing_database(tmp_path) -> None:
    database_path = tmp_path / "missing.sqlite3"

    with pytest.raises(RuntimeError, match="--init-db"):
        StateStorage(database_path)


def test_init_database_creates_users_table(tmp_path) -> None:
    database_path = tmp_path / "db" / "bot.sqlite3"

    init_database(database_path)

    inspector = inspect(create_engine(database_url(database_path)))
    assert "users" in inspector.get_table_names()
    assert "future_messages" in inspector.get_table_names()


def test_state_storage_persists_user_state(tmp_path) -> None:
    database_path = tmp_path / "bot.sqlite3"
    init_database(database_path)
    storage = StateStorage(database_path)

    storage.set(42, "kk1", "kk20_answer")
    state = storage.get(42)

    assert state is not None
    assert state.user_id == 42
    assert state.current_node == "kk1"
    assert state.waiting_for == "kk20_answer"
    assert state.last_message_sent_at is not None


def test_state_storage_persists_admin_users(tmp_path) -> None:
    database_path = tmp_path / "bot.sqlite3"
    init_database(database_path)
    storage = StateStorage(database_path, admin_user_ids=(42,))

    storage.set(42, "kk1")

    state = storage.get(42)

    assert state is not None
    assert state.user_id == 42
    assert state.current_node == "kk1"


def test_state_storage_schedules_due_future_messages(tmp_path) -> None:
    database_path = tmp_path / "bot.sqlite3"
    init_database(database_path)
    storage = StateStorage(database_path)
    send_at = datetime.now(UTC) - timedelta(seconds=1)

    storage.schedule_future_message(
        user_id=42,
        chat_id=4242,
        node_id="kk6",
        send_at=send_at,
        source_node_id="kk17",
    )

    due_messages = storage.due_future_messages(datetime.now(UTC))
    assert len(due_messages) == 1
    assert due_messages[0].user_id == 42
    assert due_messages[0].chat_id == 4242
    assert due_messages[0].node_id == "kk6"
    assert due_messages[0].source_node_id == "kk17"


def test_state_storage_marks_future_messages_sent(tmp_path) -> None:
    database_path = tmp_path / "bot.sqlite3"
    init_database(database_path)
    storage = StateStorage(database_path)
    now = datetime.now(UTC)

    storage.schedule_future_message(42, 4242, "kk6", now - timedelta(seconds=1), "kk17")
    storage.mark_future_message_sent(42, "kk6")

    assert storage.due_future_messages(now) == []


def test_state_storage_schedules_future_messages_for_admins(tmp_path) -> None:
    database_path = tmp_path / "bot.sqlite3"
    init_database(database_path)
    storage = StateStorage(database_path, admin_user_ids=(42,))

    storage.schedule_future_message(42, 4242, "kk6", datetime.now(UTC), "kk17")

    due_messages = storage.due_future_messages(datetime.now(UTC) + timedelta(seconds=1))

    assert len(due_messages) == 1
    assert due_messages[0].user_id == 42


def test_state_storage_counts_admin_stats(tmp_path) -> None:
    database_path = tmp_path / "bot.sqlite3"
    init_database(database_path)
    storage = StateStorage(database_path, admin_user_ids=(99,))
    now = datetime(2026, 7, 4, tzinfo=UTC)

    for user_id, node_id in (
        (1, "done"),
        (2, "kk1"),
        (3, "done"),
        (4, "done"),
        (99, "done"),
    ):
        storage.set(user_id, node_id)

    with storage.session_factory() as session:
        values = {
            1: (now - timedelta(days=40), now - timedelta(days=1)),
            2: (now - timedelta(days=3), now - timedelta(days=3)),
            3: (now - timedelta(days=20), now - timedelta(days=20)),
            4: (now - timedelta(days=40), now - timedelta(days=20)),
        }
        for user_id, (created_at, updated_at) in values.items():
            user = session.get(User, user_id)
            assert user is not None
            user.created_at = created_at
            user.updated_at = updated_at
        session.commit()

    stats = storage.admin_stats({"done"}, now)

    assert stats.total_users == 4
    assert stats.registered_last_7_days == 1
    assert stats.completed_last_7_days == 1
    assert stats.registered_last_30_days == 2
    assert stats.completed_last_30_days == 3
