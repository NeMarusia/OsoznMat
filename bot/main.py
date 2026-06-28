from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from bot.config import load_settings
from bot.db import StateStorage
from bot.engine import FlowEngine, RuntimePaths
from bot.flow_loader import load_flow, validate_flow


async def main() -> None:
    settings = load_settings()
    logging.basicConfig(level=settings.log_level)

    flow = load_flow(settings.flow_path)
    errors = validate_flow(flow)
    if errors:
        raise RuntimeError("Invalid flow:\n" + "\n".join(errors))

    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()
    engine = FlowEngine(
        flow=flow,
        storage=StateStorage(settings.database_path),
        paths=RuntimePaths(images_dir=settings.images_dir, videos_dir=settings.videos_dir),
    )

    @dispatcher.message(CommandStart())
    async def start(message: Message) -> None:
        await engine.start(bot, message)

    @dispatcher.callback_query(F.data.startswith("goto:"))
    async def callback(callback_query: CallbackQuery) -> None:
        await callback_query.answer()
        if not callback_query.message:
            return
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            logging.exception("Failed to delete message with inline keyboard")
        await engine.handle_callback(
            bot,
            callback_query.message.chat.id,
            callback_query.from_user.id,
            callback_query.data,
        )

    @dispatcher.message(F.text)
    async def text(message: Message) -> None:
        await engine.handle_text(bot, message)

    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
