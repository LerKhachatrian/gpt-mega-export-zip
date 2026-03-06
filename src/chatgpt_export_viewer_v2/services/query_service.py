from __future__ import annotations

from ..domain.enums import SortMode, ThreadTypeFilter
from ..domain.models import ThreadSummary


class QueryService:
    def apply(
        self,
        rows: list[ThreadSummary],
        query: str,
        shared_only: bool,
        parse_health: str,
        sort_mode: SortMode,
        thread_type: ThreadTypeFilter,
        coding_threshold: float,
        min_coding_confidence: float,
    ) -> list[ThreadSummary]:
        filtered = list(rows)
        q = (query or "").strip().lower()
        if isinstance(thread_type, str):
            try:
                thread_type = ThreadTypeFilter(thread_type)
            except ValueError:
                thread_type = ThreadTypeFilter.ALL
        threshold = min(1.0, max(0.0, float(coding_threshold)))
        min_conf = min(1.0, max(0.0, float(min_coding_confidence)))

        if shared_only:
            filtered = [row for row in filtered if row.is_shared]

        if parse_health != "all":
            filtered = [row for row in filtered if row.parse_health == parse_health]

        if thread_type == ThreadTypeFilter.PRIMARY_CODING:
            filtered = [row for row in filtered if (row.code_chars + row.non_code_chars) > 0 and row.code_ratio >= threshold]
        elif thread_type == ThreadTypeFilter.NON_CODING:
            filtered = [row for row in filtered if (row.code_chars + row.non_code_chars) > 0 and row.code_ratio < threshold]

        if min_conf > 0:
            filtered = [row for row in filtered if row.coding_confidence >= min_conf]

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
        elif sort_mode == SortMode.TOKENS:
            filtered.sort(key=lambda row: (row.tokens_o200k, row.total_messages, row.words), reverse=True)
        elif sort_mode == SortMode.CODE_RATIO:
            filtered.sort(key=lambda row: (row.code_ratio, row.coding_confidence, row.total_messages), reverse=True)
        elif sort_mode == SortMode.CODING_CONFIDENCE:
            filtered.sort(key=lambda row: (row.coding_confidence, row.code_ratio, row.total_messages), reverse=True)
        elif sort_mode == SortMode.TITLE:
            filtered.sort(key=lambda row: (row.title or "").lower())
        else:
            filtered.sort(key=lambda row: row.updated_at or 0, reverse=True)

        return filtered
