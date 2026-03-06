from __future__ import annotations

import re

_PROMPT_RE = re.compile(r"^(\$|#|PS>|>>>|\.\/|npm\s|pnpm\s|yarn\s|pip\s|python\s|node\s|git\s)")
_FLAG_RE = re.compile(r"\s--[A-Za-z0-9][A-Za-z0-9-_]*")
_PATH_RE = re.compile(r"(\/[A-Za-z0-9._-]+)+|([A-Za-z]:\\\\[A-Za-z0-9._\\-]+)")


def is_command_like_line(line: str) -> bool:
    text = line.strip()
    if not text:
        return False

    if _PROMPT_RE.search(text):
        return True
    if _FLAG_RE.search(text) and len(text.split()) >= 2:
        return True
    if _PATH_RE.search(text) and any(token in text for token in ("cat ", "ls ", "cd ", "mkdir ", "rm ", "cp ", "mv ")):
        return True
    return False
