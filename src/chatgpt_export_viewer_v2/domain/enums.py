from __future__ import annotations

from enum import Enum


class SortMode(str, Enum):
    UPDATED = "updated"
    CREATED = "created"
    MESSAGES = "messages"
    WORDS = "words"
    TOKENS = "tokens"
    CODE_RATIO = "code_ratio"
    CODING_CONFIDENCE = "coding_confidence"
    TITLE = "title"


class LoadState(str, Enum):
    IDLE = "idle"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"


class ThreadTypeFilter(str, Enum):
    ALL = "all"
    PRIMARY_CODING = "primary_coding"
    NON_CODING = "non_coding"
