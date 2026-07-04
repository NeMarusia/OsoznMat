from __future__ import annotations

import asyncio
import argparse
from contextlib import suppress
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from bot.config import load_database_path, load_settings
from bot.db import AdminStats, StateStorage, init_database
from bot.engine import FlowEngine, RuntimePaths
from bot.flow_loader import Flow, load_flow, validate_flow
from bot.keyboards import find_button_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="initialize or migrate the SQLite database and print the DATABASE_PATH value for .env",
    )
    return parser.parse_args()


def completed_node_ids(flow: Flow) -> set[str]:
    node_ids: set[str] = set()
    for node_id, node in flow.nodes.items():
        buttons = node.get("buttons") or []
        has_transition_button = any(button.get("target") for button in buttons)
        has_transition = any(
            node.get(field)
            for field in ("next", "text_target", "input_handler", "timeout_target")
        )
        if not has_transition and not has_transition_button:
            node_ids.add(node_id)
    return node_ids


def format_admin_status(stats: AdminStats) -> str:
    return (
        "Раздел администратора.\n\n"
        f"Пользователей всего: {stats.total_users}\n"
        "За последние 7 дней:\n"
        f"- зарегистрировались: {stats.registered_last_7_days}\n"
        f"- полностью прошли диалог: {stats.completed_last_7_days}\n"
        "За последние 30 дней:\n"
        f"- зарегистрировались: {stats.registered_last_30_days}\n"
        f"- полностью прошли диалог: {stats.completed_last_30_days}"
    )


async def run_bot() -> None:
    settings = load_settings()
    logging.basicConfig(level=settings.log_level)

    flow = load_flow(settings.flow_path)
    errors = validate_flow(flow)
    if errors:
        raise RuntimeError("Invalid flow:\n" + "\n".join(errors))

    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()
    storage = StateStorage(settings.database_path, settings.admin_user_ids)
    completed_nodes = completed_node_ids(flow)
    engine = FlowEngine(
        flow=flow,
        storage=storage,
        paths=RuntimePaths(images_dir=settings.images_dir, videos_dir=settings.videos_dir),
    )

    @dispatcher.message(CommandStart())
    async def start(message: Message) -> None:
        await engine.start(bot, message)

    @dispatcher.message(Command("status"))
    async def status(message: Message) -> None:
        if not message.from_user or message.from_user.id not in settings.admin_user_ids:
            return
        await message.answer(format_admin_status(storage.admin_stats(completed_nodes)))

    @dispatcher.callback_query(F.data.startswith("goto:"))
    async def callback(callback_query: CallbackQuery) -> None:
        await callback_query.answer()
        if not callback_query.message:
            return
        button_text = find_button_text(callback_query.message.reply_markup, callback_query.data)
        selected_text = button_text or "выбранный вариант"
        try:
            await callback_query.message.edit_text(
                text=f'Выбран вариант "{selected_text}"',
                reply_markup=None,
            )
        except TelegramBadRequest:
            logging.exception("Failed to update message with selected button")
        await engine.handle_callback(
            bot,
            callback_query.message.chat.id,
            callback_query.from_user.id,
            callback_query.data,
        )

    @dispatcher.message(F.text)
    async def text(message: Message) -> None:
        await engine.handle_text(bot, message)

    await engine.dispatch_due_future_messages(bot)
    future_messages_task = asyncio.create_task(
        engine.run_future_message_dispatcher(bot, settings.future_messages_check_period)
    )
    try:
        await dispatcher.start_polling(bot)
    finally:
        future_messages_task.cancel()
        with suppress(asyncio.CancelledError):
            await future_messages_task


def init_db_command() -> None:
    database_path = load_database_path()
    init_database(database_path)
    print("Database initialized.")
    print("Add this to .env:")
    print(f"DATABASE_PATH={database_path}")


def main() -> None:
    args = parse_args()
    try:
        if args.init_db:
            init_db_command()
            return
        asyncio.run(run_bot())
    except RuntimeError as error:
        raise SystemExit(f"Error: {error}") from error


if __name__ == "__main__":
    main()
