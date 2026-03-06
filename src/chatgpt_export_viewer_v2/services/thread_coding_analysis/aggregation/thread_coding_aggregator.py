from __future__ import annotations

from .message_coding_aggregator import analyze_message_text
from ..thread_coding_models import ThreadCodingSignals
from ..thread_coding_policy import ThreadCodingPolicy


def aggregate_thread_messages(messages: list[str], policy: ThreadCodingPolicy) -> ThreadCodingSignals:
    signals = ThreadCodingSignals()
    for text in messages:
        analyze_message_text(text=text, signals=signals, policy=policy)
    return signals
