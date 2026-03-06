from __future__ import annotations

from ....services.thread_coding_analysis import ThreadCodingClassifier
from ....services.thread_coding_analysis.thread_coding_models import ThreadCodingClassification


class CodingEnrichmentWorker:
    def __init__(self) -> None:
        self._classifier = ThreadCodingClassifier()

    def classify(self, message_texts: list[str], threshold: float) -> ThreadCodingClassification:
        return self._classifier.classify(messages=message_texts, threshold=threshold)
