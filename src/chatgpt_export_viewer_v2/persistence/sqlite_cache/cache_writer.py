from __future__ import annotations

import json
import zlib
from decimal import Decimal
from pathlib import Path

from ...data import parser_stream
from ...data.normalizer import build_details
from ...domain.models import HealthEvent, ThreadSummary
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

        total_rows = 0

        files: list[tuple[Path, bool]] = []
        regular = source_path / "conversations.json"
        shared = source_path / "shared_conversations.json"
        if regular.exists():
            files.append((regular, False))
        if shared.exists():
            files.append((shared, True))

        for file_path, is_shared in files:
            if is_cancelled():
                break

            file_chunk: list[ThreadSummary] = []
            rows_in_file = 0

            for obj, percent, note in parser_stream.iter_thread_objects_with_progress(
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
                        user_messages, assistant_messages, words, snippet,
                        source_file, is_shared, parse_health
                    ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

                serialized = json.dumps(obj, ensure_ascii=False, default=_json_default).encode("utf-8", errors="ignore")
                compressed = zlib.compress(serialized, level=6)
                blob.execute(
                    """
                    INSERT OR REPLACE INTO thread_raw(thread_id, raw_json, compressed)
                    VALUES(?, ?, 1)
                    """,
                    (summary.thread_id, compressed),
                )

                rows_in_file += 1
                total_rows += 1
                file_chunk.append(summary)

                if len(file_chunk) >= parse_chunk_size:
                    hot.commit()
                    blob.commit()
                    on_batch(file_chunk)
                    file_chunk = []

                if rows_in_file == 1 or rows_in_file % 25 == 0:
                    on_progress(percent, f"Building cache from {file_path.name} | indexed {rows_in_file:,} threads")

            if file_chunk:
                hot.commit()
                blob.commit()
                on_batch(file_chunk)

            on_progress(100, f"Built cache chunk for {file_path.name} | rows: {rows_in_file:,}")

        if not is_cancelled():
            hot.commit()
            blob.commit()

        # Persist warning/info events if emitted during build.
        if is_cancelled():
            on_health([HealthEvent(level="warning", code="build_cancelled", message="Cache build was cancelled")])

        hot.close()
        blob.close()
        return total_rows
