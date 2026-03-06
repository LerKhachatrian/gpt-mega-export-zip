from __future__ import annotations

import json
import time
import zlib
from decimal import Decimal
from pathlib import Path

from ...config.defaults import DEFAULT_CODING_THRESHOLD
from ...data import parser_stream
from ...data.normalizer import build_details
from ...domain.models import HealthEvent, ThreadSummary
from .analysis_enrichment import (
    AnalysisEnrichmentBatchWriter,
    AnalysisEnrichmentController,
    AnalysisEnrichmentTask,
)
from .schema_blob import ensure_schema_blob
from .schema_hot import ensure_schema_hot
from .sqlite_connection import open_connection


def _json_default(value):
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"Unsupported JSON type: {type(value)}")


class CacheWriter:
    def __init__(self, hot_db_tmp: Path, blob_db_tmp: Path) -> None:
        self._hot_tmp = hot_db_tmp
        self._blob_tmp = blob_db_tmp

    def build(
        self,
        source_path: Path,
        parse_chunk_size: int,
        max_json_fallback_mb: int,
        on_batch,
        on_progress,
        on_health,
        is_cancelled,
    ) -> int:
        if self._hot_tmp.exists():
            self._hot_tmp.unlink()
        if self._blob_tmp.exists():
            self._blob_tmp.unlink()

        hot = open_connection(self._hot_tmp, read_only=False)
        blob = open_connection(self._blob_tmp, read_only=False)
        ensure_schema_hot(hot)
        ensure_schema_blob(blob)

        enrichment_controller = AnalysisEnrichmentController(
            coding_threshold=DEFAULT_CODING_THRESHOLD,
            on_health=on_health,
        )
        enrichment_batch_writer = AnalysisEnrichmentBatchWriter(
            hot_connection=hot,
            chunk_size=parse_chunk_size,
            on_batch=on_batch,
        )

        enrichment_backlog_limit = max(parse_chunk_size * 2, 192)

        def drain_enrichment(
            wait_for_completion: bool,
            wait_timeout_seconds: float | None = None,
        ) -> int:
            updates = enrichment_controller.drain_updates(
                wait_for_completion=wait_for_completion,
                wait_timeout_seconds=wait_timeout_seconds,
            )
            for update in updates:
                enrichment_batch_writer.apply_update(update)
            return len(updates)

        total_rows = 0

        files: list[tuple[Path, bool]] = []
        regular = source_path / "conversations.json"
        shared = source_path / "shared_conversations.json"
        if regular.exists():
            files.append((regular, False))
        if shared.exists():
            files.append((shared, True))

        try:
            for file_path, is_shared in files:
                if is_cancelled():
                    break

                file_chunk: list[ThreadSummary] = []
                rows_in_file = 0

                for obj, percent, _note in parser_stream.iter_thread_objects_with_progress(
                    file_path=file_path,
                    max_json_fallback_mb=max_json_fallback_mb,
                    is_cancelled=is_cancelled,
                ):
                    details = build_details(obj, source_file=str(file_path), is_shared=is_shared)
                    summary = details.summary

                    hot.execute(
                        """
                        INSERT OR REPLACE INTO threads(
                            thread_id, title, created_at, updated_at, total_messages,
                            user_messages, assistant_messages, words, tokens_o200k,
                            code_chars, non_code_chars, code_ratio, coding_confidence,
                            is_primary_coding, coding_signals, snippet,
                            source_file, is_shared, parse_health
                        ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            summary.thread_id,
                            summary.title,
                            summary.created_at,
                            summary.updated_at,
                            summary.total_messages,
                            summary.user_messages,
                            summary.assistant_messages,
                            summary.words,
                            summary.tokens_o200k,
                            summary.code_chars,
                            summary.non_code_chars,
                            summary.code_ratio,
                            summary.coding_confidence,
                            int(summary.is_primary_coding),
                            summary.coding_signals,
                            summary.snippet,
                            summary.source_file,
                            int(summary.is_shared),
                            summary.parse_health,
                        ),
                    )

                    for msg_index, message in enumerate(details.messages):
                        hot.execute(
                            """
                            INSERT OR REPLACE INTO messages(
                                thread_id, msg_index, role, content, created, model, message_id
                            ) VALUES(?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                summary.thread_id,
                                msg_index,
                                message.role,
                                message.content,
                                message.created,
                                message.model,
                                message.message_id,
                            ),
                        )

                    serialized = json.dumps(obj, ensure_ascii=False, default=_json_default).encode(
                        "utf-8",
                        errors="ignore",
                    )
                    compressed = zlib.compress(serialized, level=6)
                    blob.execute(
                        """
                        INSERT OR REPLACE INTO thread_raw(thread_id, raw_json, compressed)
                        VALUES(?, ?, 1)
                        """,
                        (summary.thread_id, compressed),
                    )

                    enrichment_controller.submit(
                        AnalysisEnrichmentTask(
                            summary=summary,
                            message_texts=[message.content for message in details.messages if message.content],
                        )
                    )

                    rows_in_file += 1
                    total_rows += 1
                    file_chunk.append(summary)

                    if len(file_chunk) >= parse_chunk_size:
                        hot.commit()
                        blob.commit()
                        on_batch(file_chunk)
                        file_chunk = []

                    if enrichment_controller.pending_count() >= enrichment_backlog_limit:
                        while enrichment_controller.pending_count() >= enrichment_backlog_limit and not is_cancelled():
                            drain_enrichment(wait_for_completion=True, wait_timeout_seconds=0.35)
                    elif rows_in_file % 25 == 0:
                        drain_enrichment(wait_for_completion=False)

                    if rows_in_file == 1 or rows_in_file % 25 == 0:
                        on_progress(percent, f"Building cache from {file_path.name} | indexed {rows_in_file:,} threads")

                if file_chunk:
                    hot.commit()
                    blob.commit()
                    on_batch(file_chunk)

                drain_enrichment(wait_for_completion=False)
                enrichment_batch_writer.flush()
                on_progress(100, f"Built cache chunk for {file_path.name} | rows: {rows_in_file:,}")

            finalize_tick = 0
            while enrichment_controller.has_pending() and not is_cancelled():
                drained = drain_enrichment(wait_for_completion=True, wait_timeout_seconds=0.35)
                enrichment_batch_writer.flush()

                pending = enrichment_controller.pending_count()
                now = time.monotonic()
                if pending > 0 and (drained > 0 or now - finalize_tick >= 0.4):
                    on_progress(99, f"Finalizing analysis | pending {pending:,}")
                    finalize_tick = now

            if not is_cancelled():
                hot.commit()
                blob.commit()

            if is_cancelled():
                on_health([HealthEvent(level="warning", code="build_cancelled", message="Cache build was cancelled")])

            return total_rows
        finally:
            enrichment_batch_writer.flush()
            enrichment_controller.close()
            hot.close()
            blob.close()
