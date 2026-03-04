from __future__ import annotations


def thread_list_skeleton_rows(count: int = 24) -> list[str]:
    return [f"Loading thread {index + 1}..." for index in range(count)]


def inspector_skeleton_markdown() -> str:
    return "\n".join(
        [
            "# Loading thread...",
            "",
            "- Fetching messages",
            "- Building markdown",
            "- Hydrating metadata",
            "",
            "Please wait...",
        ]
    )
