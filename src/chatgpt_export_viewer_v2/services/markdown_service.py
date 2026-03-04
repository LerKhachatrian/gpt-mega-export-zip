from __future__ import annotations

import json
from datetime import datetime

from ..domain.models import ThreadDetails


class MarkdownService:
    def render_conversation(self, details: ThreadDetails) -> str:
        lines: list[str] = []
        summary = details.summary

        lines.append(f"# {summary.title or '(untitled)'}")
        lines.append("")
        lines.append(f"Thread ID: `{summary.thread_id}`")
        lines.append(f"Messages: {summary.total_messages}")
        lines.append(f"User/Assistant: {summary.user_messages}/{summary.assistant_messages}")
        lines.append(f"Created: {self._fmt(summary.created_at)}")
        lines.append(f"Updated: {self._fmt(summary.updated_at)}")
        lines.append("")
        lines.append("---")
        lines.append("")

        if not details.messages:
            lines.append("_No visible messages in this thread._")
            return "\n".join(lines)

        for i, message in enumerate(details.messages):
            lines.append(f"## {message.role.capitalize()}")
            meta_bits: list[str] = []
            if message.created is not None:
                meta_bits.append(f"time: {self._fmt(message.created)}")
            if message.model:
                meta_bits.append(f"model: {message.model}")
            if meta_bits:
                lines.append(f"_{' | '.join(meta_bits)}_")
            lines.append("")
            lines.append(message.content)
            if i != len(details.messages) - 1:
                lines.append("")

        return "\n".join(lines)

    def render_timeline(self, details: ThreadDetails) -> str:
        lines = ["# Timeline", ""]
        if not details.messages:
            lines.append("_No timeline data._")
            return "\n".join(lines)

        for idx, message in enumerate(details.messages, start=1):
            lines.append(
                f"{idx}. `{self._fmt(message.created)}` - **{message.role}** ({len(message.content.split())} words)"
            )
        return "\n".join(lines)

    def render_metadata(self, details: ThreadDetails) -> str:
        summary = details.summary
        lines = [
            "# Metadata",
            "",
            f"- Thread ID: `{summary.thread_id}`",
            f"- Source file: `{summary.source_file}`",
            f"- Shared thread: `{summary.is_shared}`",
            f"- Parse health: `{summary.parse_health}`",
            f"- Messages: `{summary.total_messages}`",
            f"- Words: `{summary.words}`",
            f"- Created: `{self._fmt(summary.created_at)}`",
            f"- Updated: `{self._fmt(summary.updated_at)}`",
        ]
        return "\n".join(lines)

    def render_raw(self, details: ThreadDetails) -> str:
        payload = details.raw or {}
        serialized = json.dumps(payload, ensure_ascii=False, indent=2)
        if len(serialized) > 250_000:
            serialized = serialized[:250_000] + "\n...<truncated>"
        return "```json\n" + serialized + "\n```"

    @staticmethod
    def _fmt(value: float | None) -> str:
        if value is None:
            return "n/a"
        try:
            return datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return str(value)
