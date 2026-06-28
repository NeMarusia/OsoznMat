from bot.answer_parser import is_kk20_correct, parse_digit_answer


def test_parse_digit_answer_extracts_numbers() -> None:
    assert parse_digit_answer("4, 5") == ("4", "5")
    assert parse_digit_answer("ответы: 5;4") == ("5", "4")


def test_kk20_accepts_expected_answer_variants() -> None:
    valid_answers = ["45", "54", "4 5", "5 4", "4,5", "5,4", "4;5", "5;4", "4 и 5"]
    for answer in valid_answers:
        assert is_kk20_correct(answer), answer


def test_kk20_rejects_incomplete_or_extra_answers() -> None:
    invalid_answers = ["4", "5", "35", "53", "3 5", "5 3", "3,5", "5,3", "1 4 5", ""]
    for answer in invalid_answers:
        assert not is_kk20_correct(answer), answer

