import pytest

from bot.config import parse_admin_user_ids


def test_parse_admin_user_ids_accepts_comma_separated_values() -> None:
    assert parse_admin_user_ids("1,2, 3") == (1, 2, 3)


def test_parse_admin_user_ids_ignores_empty_values() -> None:
    assert parse_admin_user_ids("1,, 2, ") == (1, 2)


def test_parse_admin_user_ids_rejects_non_integer_values() -> None:
    with pytest.raises(RuntimeError, match="BOT_ADMIN_USERS"):
        parse_admin_user_ids("1, user, 2")
