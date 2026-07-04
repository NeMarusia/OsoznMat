from bot.keyboards import build_keyboard, find_button_text
from bot.main import format_selected_button_message


def test_find_button_text_returns_matching_callback_button_text() -> None:
    markup = build_keyboard(
        [
            {"text": "Первый вариант", "target": "kk1"},
            {"text": "Второй вариант", "target": "kk2"},
        ]
    )

    assert find_button_text(markup, "goto:kk2") == "Второй вариант"


def test_find_button_text_ignores_missing_callback_data() -> None:
    markup = build_keyboard([{"text": "Первый вариант", "target": "kk1"}])

    assert find_button_text(markup, "goto:kk2") is None


def test_format_selected_button_message_appends_selected_button_text() -> None:
    assert (
        format_selected_button_message("Исходный текст", "Первый вариант")
        == 'Исходный текст\n\nВыбран вариант "Первый вариант"'
    )


def test_format_selected_button_message_handles_missing_original_text() -> None:
    assert format_selected_button_message(None, "Первый вариант") == 'Выбран вариант "Первый вариант"'
