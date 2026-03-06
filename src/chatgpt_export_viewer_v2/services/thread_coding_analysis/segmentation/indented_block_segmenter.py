from __future__ import annotations


def split_lines(text: str) -> list[str]:
    if not text:
        return []
    return text.splitlines()


def is_indented_code_line(line: str) -> bool:
    if not line:
        return False
    return line.startswith("    ") or line.startswith("\t")
