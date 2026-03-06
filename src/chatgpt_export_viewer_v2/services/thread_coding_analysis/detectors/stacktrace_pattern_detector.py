from __future__ import annotations

import re

_TRACE_PREFIX_RE = re.compile(r"^(Traceback \(most recent call last\):|at\s+.+\(.+\)|File \".+\", line \d+)")
_ERROR_TOKEN_RE = re.compile(r"\b(Exception|Error|TypeError|ValueError|ReferenceError|SyntaxError)\b")


def is_stacktrace_line(line: str) -> bool:
    text = line.strip()
    if not text:
        return False
    if _TRACE_PREFIX_RE.search(text):
        return True
    if _ERROR_TOKEN_RE.search(text) and (":" in text or " at " in text):
        return True
    return False
