from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

from ....domain.models import HealthEvent
from ....services.thread_coding_analysis.thread_coding_models import ThreadCodingClassification
from .analysis_enrichment_models import AnalysisEnrichmentTask, AnalysisEnrichmentUpdate, PendingAnalysisJob
from .analysis_enrichment_queue import AnalysisEnrichmentQueue
from .coding_enrichment_worker import CodingEnrichmentWorker
from .token_enrichment_worker import TokenEnrichmentWorker


class AnalysisEnrichmentController:
    def __init__(self, coding_threshold: float, on_health) -> None:
        self._coding_threshold = min(1.0, max(0.0, float(coding_threshold)))
        self._on_health = on_health
        self._queue = AnalysisEnrichmentQueue()

        self._token_worker = TokenEnrichmentWorker()
        self._coding_worker = CodingEnrichmentWorker()

        self._token_executor = (
            ThreadPoolExecutor(max_workers=1, thread_name_prefix="o200k-token")
            if self._token_worker.available
            else None
        )
        if self._token_executor is None:
            self._emit_health(
                level="warning",
                code="o200k_unavailable",
                message="tiktoken/o200k_base unavailable; token stats disabled for this cache build",
            )

        self._coding_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="thread-coding")

    def submit(self, task: AnalysisEnrichmentTask) -> None:
        token_future = None
        if self._token_executor is not None:
            token_future = self._token_executor.submit(self._token_worker.count_tokens, task.message_texts)

        coding_future = self._coding_executor.submit(self._coding_worker.classify, task.message_texts, self._coding_threshold)
        self._queue.add(PendingAnalysisJob(task=task, token_future=token_future, coding_future=coding_future))

    def pending_count(self) -> int:
        return self._queue.count()

    def has_pending(self) -> bool:
        return self._queue.has_pending()

    def drain_updates(
        self,
        wait_for_completion: bool,
        wait_timeout_seconds: float | None = None,
    ) -> list[AnalysisEnrichmentUpdate]:
        jobs = self._queue.pending()
        if wait_for_completion and jobs:
            futures = set()
            for job in jobs:
                if job.token_future is not None:
                    futures.add(job.token_future)
                if job.coding_future is not None:
                    futures.add(job.coding_future)
            if futures:
                wait_kwargs = {"return_when": FIRST_COMPLETED}
                if wait_timeout_seconds is not None and wait_timeout_seconds > 0:
                    wait_kwargs["timeout"] = float(wait_timeout_seconds)
                wait(futures, **wait_kwargs)

        updates: list[AnalysisEnrichmentUpdate] = []
        remaining: list[PendingAnalysisJob] = []

        for job in jobs:
            token_done = job.token_future is None or job.token_future.done()
            coding_done = job.coding_future is None or job.coding_future.done()
            if not token_done or not coding_done:
                remaining.append(job)
                continue

            tokens_o200k = 0
            if job.token_future is not None:
                try:
                    tokens_o200k = int(job.token_future.result() or 0)
                except Exception as exc:
                    self._emit_health(
                        level="warning",
                        code="token_count_failed",
                        message=f"Token counting failed for thread {job.task.summary.thread_id}: {exc}",
                    )

            coding_result: ThreadCodingClassification
            try:
                coding_result = (
                    job.coding_future.result()
                    if job.coding_future is not None
                    else ThreadCodingClassification(
                        code_chars=0,
                        non_code_chars=0,
                        code_ratio=0.0,
                        confidence=0.0,
                        is_primary_coding=False,
                        signal_summary="coding_future_missing",
                    )
                )
            except Exception as exc:
                self._emit_health(
                    level="warning",
                    code="coding_classification_failed",
                    message=f"Coding classification failed for thread {job.task.summary.thread_id}: {exc}",
                )
                coding_result = ThreadCodingClassification(
                    code_chars=0,
                    non_code_chars=0,
                    code_ratio=0.0,
                    confidence=0.0,
                    is_primary_coding=False,
                    signal_summary="classification_error",
                )

            updates.append(
                AnalysisEnrichmentUpdate(
                    summary=job.task.summary,
                    tokens_o200k=tokens_o200k,
                    code_chars=int(coding_result.code_chars),
                    non_code_chars=int(coding_result.non_code_chars),
                    code_ratio=float(coding_result.code_ratio),
                    coding_confidence=float(coding_result.confidence),
                    is_primary_coding=bool(coding_result.is_primary_coding),
                    coding_signals=str(coding_result.signal_summary or ""),
                )
            )

        self._queue.replace(remaining)
        return updates

    def close(self) -> None:
        if self._token_executor is not None:
            self._token_executor.shutdown(wait=True, cancel_futures=True)
        self._coding_executor.shutdown(wait=True, cancel_futures=True)

    def _emit_health(self, level: str, code: str, message: str) -> None:
        self._on_health([HealthEvent(level=level, code=code, message=message)])
