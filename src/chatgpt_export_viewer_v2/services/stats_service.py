from __future__ import annotations

from ..domain.models import GlobalStats, HealthEvent, ThreadSummary


class StatsService:
    def global_stats(self, rows: list[ThreadSummary], health: list[HealthEvent], coding_threshold: float) -> GlobalStats:
        coding_threshold = min(1.0, max(0.0, float(coding_threshold)))

        classified_rows = [row for row in rows if (row.code_chars + row.non_code_chars) > 0]
        pending_rows = [row for row in rows if (row.code_chars + row.non_code_chars) <= 0]

        coding_rows = [row for row in classified_rows if row.code_ratio >= coding_threshold]
        non_coding_rows = [row for row in classified_rows if row.code_ratio < coding_threshold]

        total_threads = len(rows)
        classification_ready_threads = len(classified_rows)
        classification_pending_threads = len(pending_rows)
        shared_threads = sum(1 for row in rows if row.is_shared)

        total_messages = sum(row.total_messages for row in rows)
        total_words = sum(row.words for row in rows)
        total_tokens_o200k = sum(row.tokens_o200k for row in rows)

        coding_threads = len(coding_rows)
        non_coding_threads = len(non_coding_rows)

        coding_messages = sum(row.total_messages for row in coding_rows)
        coding_words = sum(row.words for row in coding_rows)
        coding_tokens_o200k = sum(row.tokens_o200k for row in coding_rows)

        non_coding_messages = sum(row.total_messages for row in non_coding_rows)
        non_coding_words = sum(row.words for row in non_coding_rows)
        non_coding_tokens_o200k = sum(row.tokens_o200k for row in non_coding_rows)

        pending_messages = sum(row.total_messages for row in pending_rows)
        pending_words = sum(row.words for row in pending_rows)
        pending_tokens_o200k = sum(row.tokens_o200k for row in pending_rows)

        parse_ok = sum(1 for row in rows if row.parse_health == "ok")
        parse_partial = total_threads - parse_ok

        avg_messages = (total_messages / total_threads) if total_threads else 0.0
        avg_words = (total_words / total_threads) if total_threads else 0.0
        avg_tokens_o200k = (total_tokens_o200k / total_threads) if total_threads else 0.0

        avg_code_ratio = (
            sum(row.code_ratio for row in classified_rows) / classification_ready_threads
            if classification_ready_threads
            else 0.0
        )

        avg_coding_messages = (coding_messages / coding_threads) if coding_threads else 0.0
        avg_coding_words = (coding_words / coding_threads) if coding_threads else 0.0
        avg_coding_tokens_o200k = (coding_tokens_o200k / coding_threads) if coding_threads else 0.0

        avg_non_coding_messages = (non_coding_messages / non_coding_threads) if non_coding_threads else 0.0
        avg_non_coding_words = (non_coding_words / non_coding_threads) if non_coding_threads else 0.0
        avg_non_coding_tokens_o200k = (non_coding_tokens_o200k / non_coding_threads) if non_coding_threads else 0.0

        coding_share_pct = (coding_threads / classification_ready_threads) if classification_ready_threads else 0.0

        return GlobalStats(
            total_threads=total_threads,
            classification_ready_threads=classification_ready_threads,
            classification_pending_threads=classification_pending_threads,
            shared_threads=shared_threads,
            total_messages=total_messages,
            total_words=total_words,
            total_tokens_o200k=total_tokens_o200k,
            coding_threads=coding_threads,
            non_coding_threads=non_coding_threads,
            coding_messages=coding_messages,
            coding_words=coding_words,
            coding_tokens_o200k=coding_tokens_o200k,
            non_coding_messages=non_coding_messages,
            non_coding_words=non_coding_words,
            non_coding_tokens_o200k=non_coding_tokens_o200k,
            pending_messages=pending_messages,
            pending_words=pending_words,
            pending_tokens_o200k=pending_tokens_o200k,
            coding_share_pct=coding_share_pct,
            avg_messages=avg_messages,
            avg_words=avg_words,
            avg_tokens_o200k=avg_tokens_o200k,
            avg_code_ratio=avg_code_ratio,
            avg_coding_messages=avg_coding_messages,
            avg_coding_words=avg_coding_words,
            avg_coding_tokens_o200k=avg_coding_tokens_o200k,
            avg_non_coding_messages=avg_non_coding_messages,
            avg_non_coding_words=avg_non_coding_words,
            avg_non_coding_tokens_o200k=avg_non_coding_tokens_o200k,
            coding_threshold_pct=coding_threshold * 100.0,
            parse_ok=parse_ok,
            parse_partial=parse_partial,
            health_events=len(health),
        )

    def top_threads(self, rows: list[ThreadSummary], limit: int = 25) -> list[ThreadSummary]:
        ranked = sorted(
            rows,
            key=lambda row: (row.total_messages, row.code_ratio, row.tokens_o200k, row.words),
            reverse=True,
        )
        return ranked[:limit]
