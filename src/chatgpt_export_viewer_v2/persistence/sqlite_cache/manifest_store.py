from __future__ import annotations

import time
from pathlib import Path

from .sqlite_connection import open_connection


class ManifestStore:
    def __init__(self, manifest_path: Path) -> None:
        self._path = manifest_path
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        connection = open_connection(self._path, read_only=False)
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS caches (
                cache_key TEXT PRIMARY KEY,
                source_label TEXT,
                source_signature TEXT,
                files_signature TEXT,
                schema_version INTEGER,
                parser_version TEXT,
                hot_db_path TEXT,
                blob_db_path TEXT,
                total_rows INTEGER,
                built_at REAL
            );
            """
        )
        connection.commit()
        connection.close()

    def get(self, cache_key: str) -> dict | None:
        connection = open_connection(self._path, read_only=False)
        row = connection.execute(
            """
            SELECT cache_key, source_label, source_signature, files_signature,
                   schema_version, parser_version, hot_db_path, blob_db_path,
                   total_rows, built_at
            FROM caches
            WHERE cache_key = ?
            """,
            (cache_key,),
        ).fetchone()
        connection.close()
        if row is None:
            return None
        return dict(row)

    def upsert(
        self,
        cache_key: str,
        source_label: str,
        source_signature: str,
        files_signature: str,
        schema_version: int,
        parser_version: str,
        hot_db_path: Path,
        blob_db_path: Path,
        total_rows: int,
    ) -> None:
        connection = open_connection(self._path, read_only=False)
        connection.execute(
            """
            INSERT INTO caches(
                cache_key, source_label, source_signature, files_signature,
                schema_version, parser_version, hot_db_path, blob_db_path,
                total_rows, built_at
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
                source_label = excluded.source_label,
                source_signature = excluded.source_signature,
                files_signature = excluded.files_signature,
                schema_version = excluded.schema_version,
                parser_version = excluded.parser_version,
                hot_db_path = excluded.hot_db_path,
                blob_db_path = excluded.blob_db_path,
                total_rows = excluded.total_rows,
                built_at = excluded.built_at
            """,
            (
                cache_key,
                source_label,
                source_signature,
                files_signature,
                schema_version,
                parser_version,
                str(hot_db_path),
                str(blob_db_path),
                int(total_rows),
                float(time.time()),
            ),
        )
        connection.commit()
        connection.close()

    def remove(self, cache_key: str) -> None:
        connection = open_connection(self._path, read_only=False)
        connection.execute("DELETE FROM caches WHERE cache_key = ?", (cache_key,))
        connection.commit()
        connection.close()

    def list_entries(self) -> list[dict]:
        connection = open_connection(self._path, read_only=False)
        rows = connection.execute(
            """
            SELECT cache_key, source_label, source_signature, files_signature,
                   schema_version, parser_version, hot_db_path, blob_db_path,
                   total_rows, built_at
            FROM caches
            ORDER BY built_at DESC
            """
        ).fetchall()
        connection.close()
        return [dict(row) for row in rows]
