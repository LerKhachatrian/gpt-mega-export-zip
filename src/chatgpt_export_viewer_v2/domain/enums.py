from __future__ import annotations

from enum import Enum


class SortMode(str, Enum):
    UPDATED = "updated"
    CREATED = "created"
    MESSAGES = "messages"
    WORDS = "words"
    TITLE = "title"


class LoadState(str, Enum):
    IDLE = "idle"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"
