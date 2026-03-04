from __future__ import annotations

from ..domain.enums import SortMode
from ..domain.models import ThreadSummary


class QueryService:
    def apply(
        self,
        rows: list[ThreadSummary],
        query: str,
        shared_only: bool,
        parse_health: str,
        sort_mode: SortMode,
    ) -> list[ThreadSummary]:
        filtered = list(rows)
        q = (query or "").strip().lower()

        if shared_only:
            filtered = [row for row in filtered if row.is_shared]

        if parse_health != "all":
            filtered = [row for row in filtered if row.parse_health == parse_health]

        if q:
            filtered = [
                row
                for row in filtered
                if q in (row.title or "").lower()
                or q in (row.snippet or "").lower()
                or q in (row.thread_id or "").lower()
            ]

        if sort_mode == SortMode.CREATED:
            filtered.sort(key=lambda row: row.created_at or 0, reverse=True)
        elif sort_mode == SortMode.MESSAGES:
            filtered.sort(key=lambda row: (row.total_messages, row.words), reverse=True)
        elif sort_mode == SortMode.WORDS:
            filtered.sort(key=lambda row: (row.words, row.total_messages), reverse=True)
        elif sort_mode == SortMode.TITLE:
            filtered.sort(key=lambda row: (row.title or "").lower())
        else:
            filtered.sort(key=lambda row: row.updated_at or 0, reverse=True)

        return filtered
