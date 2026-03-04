from __future__ import annotations

from collections import OrderedDict

from ..domain.models import HealthEvent, ThreadDetails, ThreadSummary


class CacheStore:
    def __init__(self) -> None:
        self._summaries: OrderedDict[str, ThreadSummary] = OrderedDict()
        self._details: OrderedDict[str, ThreadDetails] = OrderedDict()
        self._health_events: list[HealthEvent] = []

    def clear(self) -> None:
        self._summaries.clear()
        self._details.clear()
        self._health_events.clear()

    def add_batch(self, rows: list[ThreadSummary]) -> None:
        for row in rows:
            if not row.thread_id:
                continue
            self._summaries[row.thread_id] = row

    def snapshot(self) -> list[ThreadSummary]:
        return list(self._summaries.values())

    def get_summary(self, thread_id: str) -> ThreadSummary | None:
        return self._summaries.get(thread_id)

    def store_details(self, details: ThreadDetails, detail_cache_limit: int) -> None:
        key = details.summary.thread_id
        if not key:
            return
        self._details[key] = details
        while len(self._details) > detail_cache_limit:
            self._details.popitem(last=False)

    def get_details(self, thread_id: str) -> ThreadDetails | None:
        return self._details.get(thread_id)

    def add_health_events(self, events: list[HealthEvent]) -> None:
        self._health_events.extend(events)

    def health_events(self) -> list[HealthEvent]:
        return list(self._health_events)
