from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from bot.db import StateStorage, init_database
from bot.engine import FlowEngine, RuntimePaths
from bot.flow_loader import Flow


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
