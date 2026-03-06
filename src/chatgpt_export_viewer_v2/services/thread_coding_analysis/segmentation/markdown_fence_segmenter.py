from __future__ import annotations

import re

_FENCE_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)


def extract_fenced_blocks(text: str) -> tuple[list[str], str]:
    if not text:
        return [], ""

    blocks = _FENCE_RE.findall(text)
    stripped = _FENCE_RE.sub("\n", text)
    return blocks, stripped
