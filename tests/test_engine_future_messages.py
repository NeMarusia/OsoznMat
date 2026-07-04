from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine, text

from bot.db import StateStorage, database_url, init_database
from bot.engine import FlowEngine, RuntimePaths
from bot.flow_loader import Flow


class FakeBot:
    def __init__(self) -> None:
        self.messages: list[tuple[int, str]] = []

    async def send_message(self, chat_id: int, text: str, **kwargs) -> None:
        self.messages.append((chat_id, text))


def test_timer_node_schedules_future_message(tmp_path) -> None:
    database_path = tmp_path / "bot.sqlite3"
    init_database(database_path)
    storage = StateStorage(database_path)
    engine = FlowEngine(
        flow=Flow(
            start="kk17",
            nodes={
                "kk17": {"id": "kk17", "type": "timer", "delay_seconds": 30, "next": "kk6"},
                "kk6": {"id": "kk6", "text": "hello"},
            },
        ),
        storage=storage,
        paths=RuntimePaths(images_dir=tmp_path, videos_dir=tmp_path),
    )

    asyncio.run(engine.send_node(bot=None, chat_id=4242, user_id=42, node_id="kk17"))

    due_messages = storage.due_future_messages(datetime.now(UTC) + timedelta(seconds=31))
    assert len(due_messages) == 1
    assert due_messages[0].user_id == 42
    assert due_messages[0].chat_id == 4242
    assert due_messages[0].node_id == "kk6"
    assert due_messages[0].source_node_id == "kk17"


def test_dispatch_due_future_message_when_user_is_still_at_source_node(tmp_path) -> None:
    database_path = tmp_path / "bot.sqlite3"
    init_database(database_path)
    storage = StateStorage(database_path)
    storage.set(42, "source")
    storage.schedule_future_message(
        user_id=42,
        chat_id=4242,
        node_id="target",
        send_at=datetime.now(UTC) - timedelta(seconds=1),
        source_node_id="source",
    )
    bot = FakeBot()
    engine = FlowEngine(
        flow=Flow(
            start="source",
            nodes={
                "source": {"id": "source", "text": "source"},
                "target": {"id": "target", "text": "target"},
            },
        ),
        storage=storage,
        paths=RuntimePaths(images_dir=tmp_path, videos_dir=tmp_path),
    )

    asyncio.run(engine.dispatch_due_future_messages(bot))

    assert bot.messages == [(4242, "target")]
    assert storage.get(42).current_node == "target"
    assert storage.due_future_messages(datetime.now(UTC)) == []


def test_dispatch_cancels_obsolete_future_message(tmp_path) -> None:
    database_path = tmp_path / "bot.sqlite3"
    init_database(database_path)
    storage = StateStorage(database_path)
    storage.set(42, "source")
    storage.schedule_future_message(
        user_id=42,
        chat_id=4242,
        node_id="target",
        send_at=datetime.now(UTC) - timedelta(seconds=1),
        source_node_id="source",
    )
    storage.set(42, "other")
    bot = FakeBot()
    engine = FlowEngine(
        flow=Flow(
            start="source",
            nodes={
                "source": {"id": "source", "text": "source"},
                "other": {"id": "other", "text": "other"},
                "target": {"id": "target", "text": "target"},
            },
        ),
        storage=storage,
        paths=RuntimePaths(images_dir=tmp_path, videos_dir=tmp_path),
    )

    asyncio.run(engine.dispatch_due_future_messages(bot))

    assert bot.messages == []
    assert storage.get(42).current_node == "other"
    assert storage.due_future_messages(datetime.now(UTC)) == []
    engine_db = create_engine(database_url(database_path))
    with engine_db.connect() as connection:
        status = connection.execute(text("select status from future_messages")).scalar_one()
    assert status == "cancelled"
