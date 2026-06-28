from __future__ import annotations

def parse_digit_answer(text: str) -> tuple[str, ...]:
    return tuple(char for char in text if char.isdigit())


def is_kk20_correct(text: str) -> bool:
    return set(parse_digit_answer(text)) == {"4", "5"}
