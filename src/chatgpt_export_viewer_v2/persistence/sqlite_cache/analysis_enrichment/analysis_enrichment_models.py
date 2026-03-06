from __future__ import annotations

from concurrent.futures import Future
from dataclasses import dataclass

from ....domain.models import ThreadSummary
from ....services.thread_coding_analysis.thread_coding_models import ThreadCodingClassification


@dataclass
class AnalysisEnrichmentTask:
    summary: ThreadSummary
    message_texts: list[str]


@dataclass
class PendingAnalysisJob:
    task: AnalysisEnrichmentTask
    token_future: Future[int] | None
    coding_future: Future[ThreadCodingClassification] | None


@dataclass
class AnalysisEnrichmentUpdate:
    summary: ThreadSummary
    tokens_o200k: int
    code_chars: int
    non_code_chars: int
    code_ratio: float
    coding_confidence: float
    is_primary_coding: bool
    coding_signals: str
