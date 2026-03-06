from __future__ import annotations

from collections import OrderedDict
from threading import Lock

try:
    import tiktoken
except Exception:  # pragma: no cover - optional dependency at import time
    tiktoken = None


class O200KTokenCounter:
    def __init__(self, max_text_cache: int = 4096) -> None:
        self._encoding = tiktoken.get_encoding("o200k_base") if tiktoken is not None else None
        self._max_text_cache = max(128, int(max_text_cache))
        self._text_cache: OrderedDict[str, int] = OrderedDict()
        self._cache_lock = Lock()

    @property
    def available(self) -> bool:
        return self._encoding is not None

    def count_texts(self, texts: list[str]) -> int:
        if self._encoding is None:
            return 0

        total = 0
        for text in texts:
            if text:
                total += self._count_text(text)
        return total

    def _count_text(self, text: str) -> int:
        with self._cache_lock:
            cached = self._text_cache.get(text)
            if cached is not None:
                self._text_cache.move_to_end(text)
                return cached

        token_count = len(self._encoding.encode(text))
        with self._cache_lock:
            self._text_cache[text] = token_count
            self._text_cache.move_to_end(text)
            while len(self._text_cache) > self._max_text_cache:
                self._text_cache.popitem(last=False)

        return token_count
