from bot.keyboards import build_keyboard, find_button_text


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
