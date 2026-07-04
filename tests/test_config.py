import pytest

from bot.config import parse_admin_user_ids, parse_positive_int


def test_parse_admin_user_ids_accepts_comma_separated_values() -> None:
    assert parse_admin_user_ids("1,2, 3") == (1, 2, 3)


def test_parse_admin_user_ids_ignores_empty_values() -> None:
    assert parse_admin_user_ids("1,, 2, ") == (1, 2)


def test_parse_admin_user_ids_rejects_non_integer_values() -> None:
    with pytest.raises(RuntimeError, match="BOT_ADMIN_USERS"):
        parse_admin_user_ids("1, user, 2")


def test_parse_positive_int_accepts_positive_integer() -> None:
    assert parse_positive_int("60", "FUTURE_MESSAGES_CHECK_PERIOD") == 60


def test_parse_positive_int_rejects_zero() -> None:
    with pytest.raises(RuntimeError, match="greater than zero"):
        parse_positive_int("0", "FUTURE_MESSAGES_CHECK_PERIOD")


def test_parse_positive_int_rejects_non_integer() -> None:
    with pytest.raises(RuntimeError, match="must be an integer"):
        parse_positive_int("minute", "FUTURE_MESSAGES_CHECK_PERIOD")
