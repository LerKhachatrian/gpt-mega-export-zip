from __future__ import annotations

import json
import zlib
from pathlib import Path

from ...domain.models import ChatMessage, HealthEvent, ThreadDetails, ThreadSummary
from .sqlite_connection import open_connection


class CacheReader:
    def __init__(self, hot_db_path: Path, blob_db_path: Path) -> None:
        self._hot_path = hot_db_path
        self._blob_path = blob_db_path

    def stream_summaries(self, chunk_size: int, on_batch) -> int:
        connection = open_connection(self._hot_path, read_only=True)
        cursor = connection.execute(
            """
            SELECT thread_id, title, created_at, updated_at, total_messages,
                   user_messages, assistant_messages, words, tokens_o200k,
                   code_chars, non_code_chars, code_ratio, coding_confidence,
                   is_primary_coding, coding_signals, snippet,
                   source_file, is_shared, parse_health
            FROM threads
            ORDER BY updated_at DESC
            """
        )

        chunk: list[ThreadSummary] = []
        total = 0

        for row in cursor:
            chunk.append(
                ThreadSummary(
                    thread_id=row["thread_id"],
                    title=row["title"] or "(untitled)",
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    total_messages=int(row["total_messages"] or 0),
                    user_messages=int(row["user_messages"] or 0),
                    assistant_messages=int(row["assistant_messages"] or 0),
                    words=int(row["words"] or 0),
                    tokens_o200k=int(row["tokens_o200k"] or 0),
                    code_chars=int(row["code_chars"] or 0),
                    non_code_chars=int(row["non_code_chars"] or 0),
                    code_ratio=float(row["code_ratio"] or 0.0),
                    coding_confidence=float(row["coding_confidence"] or 0.0),
                    is_primary_coding=bool(int(row["is_primary_coding"] or 0)),
                    coding_signals=str(row["coding_signals"] or ""),
                    snippet=row["snippet"] or "",
                    source_file=row["source_file"] or "",
                    is_shared=bool(int(row["is_shared"] or 0)),
                    parse_health=row["parse_health"] or "ok",
                )
            )
            total += 1
            if len(chunk) >= chunk_size:
                on_batch(chunk)
                chunk = []

        if chunk:
            on_batch(chunk)

        connection.close()
        return total

    def health_events(self) -> list[HealthEvent]:
        connection = open_connection(self._hot_path, read_only=True)
        rows = connection.execute(
            """
            SELECT level, code, message, thread_id, source_file
            FROM health_events
            ORDER BY id ASC
            """
        ).fetchall()
        connection.close()
        return [
            HealthEvent(
                level=str(row["level"] or "info"),
                code=str(row["code"] or "cache"),
                message=str(row["message"] or ""),
                thread_id=row["thread_id"],
                source_file=row["source_file"],
            )
            for row in rows
        ]

    def thread_details(self, thread_id: str) -> ThreadDetails | None:
        hot = open_connection(self._hot_path, read_only=True)
        thread_row = hot.execute(
            """
            SELECT thread_id, title, created_at, updated_at, total_messages,
                   user_messages, assistant_messages, words, tokens_o200k,
                   code_chars, non_code_chars, code_ratio, coding_confidence,
                   is_primary_coding, coding_signals, snippet,
                   source_file, is_shared, parse_health
            FROM threads
            WHERE thread_id = ?
            """,
            (thread_id,),
        ).fetchone()
        if thread_row is None:
            hot.close()
            return None

        message_rows = hot.execute(
            """
            SELECT msg_index, role, content, created, model, message_id
            FROM messages
            WHERE thread_id = ?
            ORDER BY msg_index ASC
            """,
            (thread_id,),
        ).fetchall()
        hot.close()

        summary = ThreadSummary(
            thread_id=thread_row["thread_id"],
            title=thread_row["title"] or "(untitled)",
            created_at=thread_row["created_at"],
            updated_at=thread_row["updated_at"],
            total_messages=int(thread_row["total_messages"] or 0),
            user_messages=int(thread_row["user_messages"] or 0),
            assistant_messages=int(thread_row["assistant_messages"] or 0),
            words=int(thread_row["words"] or 0),
            tokens_o200k=int(thread_row["tokens_o200k"] or 0),
            code_chars=int(thread_row["code_chars"] or 0),
            non_code_chars=int(thread_row["non_code_chars"] or 0),
            code_ratio=float(thread_row["code_ratio"] or 0.0),
            coding_confidence=float(thread_row["coding_confidence"] or 0.0),
            is_primary_coding=bool(int(thread_row["is_primary_coding"] or 0)),
            coding_signals=str(thread_row["coding_signals"] or ""),
            snippet=thread_row["snippet"] or "",
            source_file=thread_row["source_file"] or "",
            is_shared=bool(int(thread_row["is_shared"] or 0)),
            parse_health=thread_row["parse_health"] or "ok",
        )

        messages = [
            ChatMessage(
                role=str(row["role"] or "assistant"),
                content=str(row["content"] or ""),
                created=row["created"],
                model=row["model"],
                message_id=row["message_id"],
            )
            for row in message_rows
        ]

        raw = None
        blob = open_connection(self._blob_path, read_only=True)
        raw_row = blob.execute(
            "SELECT raw_json, compressed FROM thread_raw WHERE thread_id = ?",
            (thread_id,),
        ).fetchone()
        blob.close()

        if raw_row is not None:
            raw_bytes = raw_row["raw_json"]
            if raw_bytes is not None:
                if int(raw_row["compressed"] or 0):
                    raw_bytes = zlib.decompress(raw_bytes)
                try:
                    raw = json.loads(raw_bytes.decode("utf-8", errors="ignore"))
                except Exception:
                    raw = None

        return ThreadDetails(summary=summary, messages=messages, raw=raw)
