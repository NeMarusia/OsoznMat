from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from aiogram import Bot
from aiogram.types import Message

from bot.answer_parser import is_kk20_correct
from bot.db import StateStorage
from bot.flow_loader import Flow
from bot.keyboards import build_keyboard
from bot.media import send_media


@dataclass(frozen=True)
class RuntimePaths:
    images_dir: Path
    videos_dir: Path


class FlowEngine:
    def __init__(self, flow: Flow, storage: StateStorage, paths: RuntimePaths) -> None:
        self.flow = flow
        self.storage = storage
        self.paths = paths

    async def start(self, bot: Bot, message: Message) -> None:
        await self.send_node(bot, message.chat.id, message.from_user.id, self.flow.start)

    async def handle_callback(self, bot: Bot, chat_id: int, user_id: int, data: str) -> None:
        if not data.startswith("goto:"):
            return
        await self.send_node(bot, chat_id, user_id, data.removeprefix("goto:"))

    async def handle_text(self, bot: Bot, message: Message) -> None:
        state = self.storage.get(message.from_user.id)
        if state is None:
            await self.start(bot, message)
            return

        node = self.flow.get(state.current_node)
        handler = node.get("input_handler")
        if handler == "kk20_answer":
            target = node["correct"] if is_kk20_correct(message.text or "") else node["incorrect"]
            await self.send_node(bot, message.chat.id, message.from_user.id, target)
            return

        text_target = node.get("text_target")
        if text_target:
            await self.send_node(bot, message.chat.id, message.from_user.id, text_target)
            return

        await bot.send_message(message.chat.id, "Пожалуйста, выберите один из вариантов ниже.")

    async def send_node(self, bot: Bot, chat_id: int, user_id: int, node_id: str) -> None:
        node = self.flow.get(node_id)
        self.storage.set(user_id, node_id, node.get("input_handler"))

        text = node.get("text")
        if text:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=build_keyboard(node.get("buttons")),
                disable_web_page_preview=True,
            )

        await send_media(bot, chat_id, node.get("media", []), self.paths.images_dir, self.paths.videos_dir)

        delay = node.get("delay_seconds")
        next_node = node.get("next")
        if isinstance(delay, int) and next_node:
            await asyncio.sleep(delay)
            await self.send_node(bot, chat_id, user_id, next_node)
        elif next_node and not node.get("buttons") and not node.get("input_handler") and not node.get("text_target"):
            await self.send_node(bot, chat_id, user_id, next_node)
