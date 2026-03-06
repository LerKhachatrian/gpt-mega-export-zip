from __future__ import annotations

import re

_ASSIGNMENT_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\s*[:=]\s*.+")
_FUNCTION_RE = re.compile(r"\b(function|def|class|interface|type|public|private|const|let|var)\b")
_JSON_LIKE_RE = re.compile(r'^[\[{].*[\]}]$')
_SQL_RE = re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN|GROUP BY)\b", re.IGNORECASE)


def is_syntax_code_line(line: str) -> bool:
    text = line.strip()
    if not text:
        return False
    if _ASSIGNMENT_RE.search(text):
        return True
    if _FUNCTION_RE.search(text):
        return True
    if _JSON_LIKE_RE.search(text):
        return True
    if _SQL_RE.search(text):
        return True
    if "=>" in text or "::" in text or ";" in text:
        return True
    return False
