from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChatMessage:
    role: str
    content: str
    created: float | None = None
    model: str | None = None
    message_id: str | None = None


@dataclass
class ThreadSummary:
    thread_id: str
    title: str
    created_at: float | None
    updated_at: float | None
    total_messages: int
    user_messages: int
    assistant_messages: int
    words: int
    snippet: str
    source_file: str
    is_shared: bool
    tokens_o200k: int = 0
    code_chars: int = 0
    non_code_chars: int = 0
    code_ratio: float = 0.0
    coding_confidence: float = 0.0
    is_primary_coding: bool = False
    coding_signals: str = ""
    parse_health: str = "ok"


@dataclass
class ThreadDetails:
    summary: ThreadSummary
    messages: list[ChatMessage] = field(default_factory=list)
    raw: dict[str, Any] | None = None


@dataclass
class HealthEvent:
    level: str
    code: str
    message: str
    thread_id: str | None = None
    source_file: str | None = None


@dataclass
class GlobalStats:
    total_threads: int
    classification_ready_threads: int
    classification_pending_threads: int
    shared_threads: int
    total_messages: int
    total_words: int
    total_tokens_o200k: int
    coding_threads: int
    non_coding_threads: int
    coding_messages: int
    coding_words: int
    coding_tokens_o200k: int
    non_coding_messages: int
    non_coding_words: int
    non_coding_tokens_o200k: int
    pending_messages: int
    pending_words: int
    pending_tokens_o200k: int
    coding_share_pct: float
    avg_messages: float
    avg_words: float
    avg_tokens_o200k: float
    avg_code_ratio: float
    avg_coding_messages: float
    avg_coding_words: float
    avg_coding_tokens_o200k: float
    avg_non_coding_messages: float
    avg_non_coding_words: float
    avg_non_coding_tokens_o200k: float
    coding_threshold_pct: float
    parse_ok: int
    parse_partial: int
    health_events: int
