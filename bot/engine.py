from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import logging
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
                parse_mode=node.get("parse_mode"),
            )

        await send_media(bot, chat_id, node.get("media", []), self.paths.images_dir, self.paths.videos_dir)
        self._schedule_timeout(chat_id, user_id, node_id, node)

        delay = node.get("delay_seconds")
        next_node = node.get("next")
        if isinstance(delay, int) and next_node:
            self._schedule_delayed_transition(chat_id, user_id, node_id, next_node, delay)
        elif next_node and not node.get("buttons") and not node.get("input_handler") and not node.get("text_target"):
            await self.send_node(bot, chat_id, user_id, next_node)

    def _schedule_timeout(self, chat_id: int, user_id: int, node_id: str, node: dict) -> None:
        timeout = node.get("timeout_seconds")
        target = node.get("timeout_target")
        if not isinstance(timeout, int) or not target:
            return
        self._schedule_delayed_transition(chat_id, user_id, node_id, target, timeout)

    def _schedule_delayed_transition(
        self,
        chat_id: int,
        user_id: int,
        source_node_id: str,
        target_node_id: str,
        delay_seconds: int,
    ) -> None:
        self.storage.schedule_future_message(
            user_id=user_id,
            chat_id=chat_id,
            node_id=target_node_id,
            send_at=datetime.now(UTC) + timedelta(seconds=delay_seconds),
            source_node_id=source_node_id,
        )

    async def dispatch_due_future_messages(self, bot: Bot) -> None:
        for future_message in self.storage.due_future_messages(datetime.now(UTC)):
            state = self.storage.get(future_message.user_id)
            if future_message.source_node_id and (
                state is None or state.current_node != future_message.source_node_id
            ):
                self.storage.mark_future_message_cancelled(future_message.id)
                continue
            try:
                await self.send_node(
                    bot,
                    future_message.chat_id,
                    future_message.user_id,
                    future_message.node_id,
                )
                self.storage.mark_future_message_sent(future_message.id)
            except Exception:
                logging.exception("Failed to dispatch future message %s", future_message.id)

    async def run_future_message_dispatcher(self, bot: Bot, check_period_seconds: int) -> None:
        while True:
            await self.dispatch_due_future_messages(bot)
            await asyncio.sleep(check_period_seconds)
