from __future__ import annotations

_CODE_SYMBOLS = set("{}[]()<>:=;+-*/%&|!#@$")


def symbol_density(text: str) -> float:
    if not text:
        return 0.0
    relevant = [char for char in text if not char.isspace()]
    if not relevant:
        return 0.0
    symbols = sum(1 for char in relevant if char in _CODE_SYMBOLS)
    return float(symbols) / float(len(relevant))


def is_symbol_dense_code_line(text: str, minimum_density: float) -> bool:
    if len(text.strip()) < 8:
        return False
    return symbol_density(text) >= float(minimum_density)
