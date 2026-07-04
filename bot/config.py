from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_DATABASE_PATH = Path("db/bot.sqlite3")


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_user_ids: tuple[int, ...]
    flow_path: Path
    database_path: Path
    debug: bool
    future_messages_check_period: int
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


def parse_positive_int(raw_value: str, variable_name: str) -> int:
    try:
        value = int(raw_value)
    except ValueError as error:
        raise RuntimeError(f"{variable_name} must be an integer") from error
    if value <= 0:
        raise RuntimeError(f"{variable_name} must be greater than zero")
    return value


def parse_debug(raw_value: str) -> bool:
    return raw_value == "1"


def load_settings() -> Settings:
    load_dotenv()
    token = os.getenv("BOT_TOKEN", "")
    if not token:
        raise RuntimeError("BOT_TOKEN is required")

    return Settings(
        bot_token=token,
        admin_user_ids=parse_admin_user_ids(os.getenv("BOT_ADMIN_USERS", "")),
        flow_path=Path(os.getenv("FLOW_PATH", "data/flow.yaml")),
        database_path=load_database_path(),
        debug=parse_debug(os.getenv("DEBUG", "")),
        future_messages_check_period=parse_positive_int(
            os.getenv("FUTURE_MESSAGES_CHECK_PERIOD", "60"),
            "FUTURE_MESSAGES_CHECK_PERIOD",
        ),
        images_dir=Path(os.getenv("IMAGES_DIR", "images")),
        videos_dir=Path(os.getenv("VIDEOS_DIR", "videos")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


def load_database_path() -> Path:
    load_dotenv()
    return Path(os.getenv("DATABASE_PATH", str(DEFAULT_DATABASE_PATH)))
