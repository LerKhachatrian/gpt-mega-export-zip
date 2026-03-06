from __future__ import annotations

from .analysis_enrichment_models import AnalysisEnrichmentUpdate


class AnalysisEnrichmentBatchWriter:
    def __init__(self, hot_connection, chunk_size: int, on_batch) -> None:
        self._hot = hot_connection
        self._chunk_size = max(1, int(chunk_size))
        self._on_batch = on_batch
        self._pending_updates = []

    def apply_update(self, update: AnalysisEnrichmentUpdate) -> None:
        summary = update.summary
        summary.tokens_o200k = int(update.tokens_o200k)
        summary.code_chars = int(update.code_chars)
        summary.non_code_chars = int(update.non_code_chars)
        summary.code_ratio = float(update.code_ratio)
        summary.coding_confidence = float(update.coding_confidence)
        summary.is_primary_coding = bool(update.is_primary_coding)
        summary.coding_signals = str(update.coding_signals)

        self._hot.execute(
            """
            UPDATE threads
            SET tokens_o200k = ?,
                code_chars = ?,
                non_code_chars = ?,
                code_ratio = ?,
                coding_confidence = ?,
                is_primary_coding = ?,
                coding_signals = ?
            WHERE thread_id = ?
            """,
            (
                summary.tokens_o200k,
                summary.code_chars,
                summary.non_code_chars,
                summary.code_ratio,
                summary.coding_confidence,
                int(summary.is_primary_coding),
                summary.coding_signals,
                summary.thread_id,
            ),
        )

        self._pending_updates.append(summary)
        if len(self._pending_updates) >= self._chunk_size:
            self.flush()

    def flush(self) -> None:
        if not self._pending_updates:
            return
        self._hot.commit()
        self._on_batch(self._pending_updates)
        self._pending_updates = []
