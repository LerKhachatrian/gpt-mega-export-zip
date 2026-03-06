from __future__ import annotations

import re

_INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")


def extract_inline_code_spans(text: str) -> tuple[list[str], str]:
    if not text:
        return [], ""

    spans = [match.group(1) for match in _INLINE_CODE_RE.finditer(text)]
    stripped = _INLINE_CODE_RE.sub(" ", text)
    return spans, stripped
