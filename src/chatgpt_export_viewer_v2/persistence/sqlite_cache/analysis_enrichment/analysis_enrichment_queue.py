from __future__ import annotations

from .analysis_enrichment_models import PendingAnalysisJob


class AnalysisEnrichmentQueue:
    def __init__(self) -> None:
        self._jobs: list[PendingAnalysisJob] = []

    def add(self, job: PendingAnalysisJob) -> None:
        self._jobs.append(job)

    def pending(self) -> list[PendingAnalysisJob]:
        return list(self._jobs)

    def replace(self, jobs: list[PendingAnalysisJob]) -> None:
        self._jobs = list(jobs)

    def count(self) -> int:
        return len(self._jobs)

    def has_pending(self) -> bool:
        return bool(self._jobs)
