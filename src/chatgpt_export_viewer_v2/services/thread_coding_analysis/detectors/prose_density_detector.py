from __future__ import annotations

import re

_STOPWORD_RE = re.compile(r"\b(the|and|for|with|that|this|you|your|from|have|will|should|could|about)\b", re.IGNORECASE)


def is_prose_like_line(line: str) -> bool:
    text = line.strip()
    if not text:
        return False

    letters = sum(1 for char in text if char.isalpha())
    spaces = sum(1 for char in text if char.isspace())
    symbols = sum(1 for char in text if not char.isalnum() and not char.isspace())

    if letters == 0:
        return False

    alpha_ratio = float(letters) / float(max(1, len(text)))
    symbol_ratio = float(symbols) / float(max(1, len(text)))
    has_stopwords = _STOPWORD_RE.search(text) is not None

    return alpha_ratio >= 0.55 and symbol_ratio <= 0.08 and (spaces >= 2 or has_stopwords)
