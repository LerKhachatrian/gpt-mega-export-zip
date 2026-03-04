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
    shared_threads: int
    total_messages: int
    total_words: int
    avg_messages: float
    avg_words: float
    parse_ok: int
    parse_partial: int
    health_events: int
