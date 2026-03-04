from __future__ import annotations

from ..domain.models import GlobalStats, HealthEvent, ThreadSummary


class StatsService:
    def global_stats(self, rows: list[ThreadSummary], health: list[HealthEvent]) -> GlobalStats:
        total_threads = len(rows)
        shared_threads = sum(1 for row in rows if row.is_shared)
        total_messages = sum(row.total_messages for row in rows)
        total_words = sum(row.words for row in rows)
        parse_ok = sum(1 for row in rows if row.parse_health == "ok")
        parse_partial = total_threads - parse_ok

        avg_messages = (total_messages / total_threads) if total_threads else 0.0
        avg_words = (total_words / total_threads) if total_threads else 0.0

        return GlobalStats(
            total_threads=total_threads,
            shared_threads=shared_threads,
            total_messages=total_messages,
            total_words=total_words,
            avg_messages=avg_messages,
            avg_words=avg_words,
            parse_ok=parse_ok,
            parse_partial=parse_partial,
            health_events=len(health),
        )

    def top_threads(self, rows: list[ThreadSummary], limit: int = 25) -> list[ThreadSummary]:
        ranked = sorted(rows, key=lambda row: (row.total_messages, row.words), reverse=True)
        return ranked[:limit]
