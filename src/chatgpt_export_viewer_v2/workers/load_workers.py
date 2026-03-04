from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from ..domain.models import HealthEvent
from ..persistence.sqlite_cache.cache_orchestrator import CacheOrchestrator
from ..persistence.sqlite_cache.cache_reader import CacheReader


class SourceLoadWorker(QThread):
    progress = Signal(int, str)
    batch = Signal(list)
    health = Signal(list)
    completed = Signal(dict)
    failed = Signal(str)

    def __init__(
        self,
        source_path: Path,
        source_label: str,
        warnings: list[str],
        parse_chunk_size: int,
        max_json_fallback_mb: int,
        cache_root: Path,
        schema_version: int,
        parser_version: str,
    ) -> None:
        super().__init__()
        self._source_path = source_path
        self._source_label = source_label
        self._warnings = warnings
        self._parse_chunk_size = parse_chunk_size
        self._max_json_fallback_mb = max_json_fallback_mb
        self._cache_root = cache_root
        self._schema_version = schema_version
        self._parser_version = parser_version
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            warning_events: list[HealthEvent] = [
                HealthEvent(level="warning", code="optional_missing", message=warning)
                for warning in self._warnings
            ]
            if warning_events:
                self.health.emit(warning_events)

            orchestrator = CacheOrchestrator(
                cache_root=self._cache_root,
                schema_version=self._schema_version,
                parser_version=self._parser_version,
            )

            result = orchestrator.ensure_cache(
                source_path=self._source_path,
                source_label=self._source_label,
                parse_chunk_size=self._parse_chunk_size,
                max_json_fallback_mb=self._max_json_fallback_mb,
                on_batch=lambda rows: self.batch.emit(rows) if not self._cancelled else None,
                on_progress=lambda percent, msg: self.progress.emit(percent, msg) if not self._cancelled else None,
                on_health=lambda events: self.health.emit(events) if not self._cancelled else None,
                is_cancelled=lambda: self._cancelled,
            )

            if self._cancelled:
                self.completed.emit({"cancelled": True, "total_rows": 0})
                return

            reader = CacheReader(
                hot_db_path=result.cache_entry.hot_db_path,
                blob_db_path=result.cache_entry.blob_db_path,
            )
            db_health = reader.health_events()
            if db_health:
                self.health.emit(db_health)

            self.completed.emit(
                {
                    "cancelled": False,
                    "total_rows": result.cache_entry.total_rows,
                    "cache_key": result.cache_entry.cache_key,
                    "cache_built": result.cache_built,
                    "hot_db_path": str(result.cache_entry.hot_db_path),
                    "blob_db_path": str(result.cache_entry.blob_db_path),
                }
            )
        except Exception as exc:
            self.failed.emit(str(exc))


class ThreadDetailsWorker(QThread):
    loaded = Signal(object)
    failed = Signal(str)

    def __init__(self, hot_db_path: Path, blob_db_path: Path, thread_id: str) -> None:
        super().__init__()
        self._hot_db_path = hot_db_path
        self._blob_db_path = blob_db_path
        self._thread_id = thread_id
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            if self._cancelled:
                return
            reader = CacheReader(hot_db_path=self._hot_db_path, blob_db_path=self._blob_db_path)
            details = reader.thread_details(self._thread_id)
            if self._cancelled:
                return
            if details is None:
                raise FileNotFoundError("Thread not found")
            self.loaded.emit(details)
        except Exception as exc:
            self.failed.emit(str(exc))
