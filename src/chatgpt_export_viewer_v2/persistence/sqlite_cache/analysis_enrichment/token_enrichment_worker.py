from __future__ import annotations

from ....services.token_count_service import O200KTokenCounter


class TokenEnrichmentWorker:
    def __init__(self) -> None:
        self._counter = O200KTokenCounter()

    @property
    def available(self) -> bool:
        return self._counter.available

    def count_tokens(self, message_texts: list[str]) -> int:
        return int(self._counter.count_texts(message_texts))
