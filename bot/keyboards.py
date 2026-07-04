from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def build_keyboard(buttons: list[dict] | None) -> InlineKeyboardMarkup | None:
    if not buttons:
        return None

    rows: list[list[InlineKeyboardButton]] = []
    for button in buttons:
        text = button["text"]
        if button.get("url"):
            rows.append([InlineKeyboardButton(text=text, url=button["url"])])
        else:
            rows.append([InlineKeyboardButton(text=text, callback_data=f"goto:{button['target']}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def find_button_text(markup: InlineKeyboardMarkup | None, callback_data: str | None) -> str | None:
    if not markup or not callback_data:
        return None
    for row in markup.inline_keyboard:
        for button in row:
            if button.callback_data == callback_data:
                return button.text
    return None
