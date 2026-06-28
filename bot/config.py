from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    flow_path: Path
    database_path: Path
    images_dir: Path
    videos_dir: Path
    log_level: str = "INFO"


def load_settings() -> Settings:
    load_dotenv()
    token = os.getenv("BOT_TOKEN", "")
    if not token:
        raise RuntimeError("BOT_TOKEN is required")

    return Settings(
        bot_token=token,
        flow_path=Path(os.getenv("FLOW_PATH", "data/flow.yaml")),
        database_path=Path(os.getenv("DATABASE_PATH", "storage/bot.sqlite3")),
        images_dir=Path(os.getenv("IMAGES_DIR", "images")),
        videos_dir=Path(os.getenv("VIDEOS_DIR", "videos")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )

