from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_user_ids: tuple[int, ...]
    flow_path: Path
    database_path: Path
    images_dir: Path
    videos_dir: Path
    log_level: str = "INFO"


def parse_admin_user_ids(raw_value: str) -> tuple[int, ...]:
    user_ids: list[int] = []
    for item in raw_value.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            user_ids.append(int(item))
        except ValueError as error:
            raise RuntimeError("BOT_ADMIN_USERS must contain comma-separated integer IDs") from error
    return tuple(user_ids)


def load_settings() -> Settings:
    load_dotenv()
    token = os.getenv("BOT_TOKEN", "")
    if not token:
        raise RuntimeError("BOT_TOKEN is required")

    return Settings(
        bot_token=token,
        admin_user_ids=parse_admin_user_ids(os.getenv("BOT_ADMIN_USERS", "")),
        flow_path=Path(os.getenv("FLOW_PATH", "data/flow.yaml")),
        database_path=Path(os.getenv("DATABASE_PATH", "storage/bot.sqlite3")),
        images_dir=Path(os.getenv("IMAGES_DIR", "images")),
        videos_dir=Path(os.getenv("VIDEOS_DIR", "videos")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
