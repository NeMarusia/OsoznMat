from __future__ import annotations

from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile, InputMediaPhoto


async def send_media(bot: Bot, chat_id: int, media: list[dict], images_dir: Path, videos_dir: Path) -> None:
    if not media:
        return

    if len(media) > 1 and all(item["type"] == "photo" for item in media):
        group = [
            InputMediaPhoto(media=FSInputFile(resolve_path(item["path"], images_dir, videos_dir)))
            for item in media
        ]
        await bot.send_media_group(chat_id=chat_id, media=group)
        return

    for item in media:
        path = resolve_path(item["path"], images_dir, videos_dir)
        if item["type"] == "photo":
            await bot.send_photo(chat_id=chat_id, photo=FSInputFile(path))
        elif item["type"] == "video":
            await bot.send_video(chat_id=chat_id, video=FSInputFile(path))
        else:
            await bot.send_document(chat_id=chat_id, document=FSInputFile(path))


def resolve_path(path: str, images_dir: Path, videos_dir: Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    if path.startswith(("images/", "videos/", "files/")):
        return candidate
    if candidate.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
        return images_dir / candidate
    return videos_dir / candidate
