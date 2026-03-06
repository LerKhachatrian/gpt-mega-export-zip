from __future__ import annotations

from .aggregation.thread_coding_aggregator import aggregate_thread_messages
from .thread_coding_confidence import compute_coding_confidence
from .thread_coding_explainer import build_signal_summary
from .thread_coding_models import ThreadCodingClassification
from .thread_coding_policy import ThreadCodingPolicy


class ThreadCodingClassifier:
    def __init__(self, policy: ThreadCodingPolicy | None = None) -> None:
        self._policy = policy or ThreadCodingPolicy()

    def classify(self, messages: list[str], threshold: float | None = None) -> ThreadCodingClassification:
        policy = self._policy
        effective_threshold = float(threshold if threshold is not None else policy.primary_threshold)

        signals = aggregate_thread_messages(messages=messages, policy=policy)
        code_ratio = signals.code_ratio
        confidence = compute_coding_confidence(
            code_ratio=code_ratio,
            total_chars=signals.total_chars,
            threshold=effective_threshold,
        )

        is_primary = code_ratio >= effective_threshold and signals.total_chars > 0
        signal_summary = build_signal_summary(signals)

        return ThreadCodingClassification(
            code_chars=int(signals.code_chars),
            non_code_chars=int(signals.non_code_chars),
            code_ratio=float(code_ratio),
            confidence=float(confidence),
            is_primary_coding=bool(is_primary),
            signal_summary=signal_summary,
        )
