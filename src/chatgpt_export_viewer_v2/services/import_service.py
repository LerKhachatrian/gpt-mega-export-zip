from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from ..config.defaults import (
    CACHE_PARSER_VERSION,
    CACHE_ROOT_DIR,
    CACHE_SCHEMA_VERSION,
    DETAIL_CACHE_LIMIT,
)
from ..data.cache_store import CacheStore
from ..data.source_resolver import SourceDescriptor, SourceResolver
from ..domain.models import HealthEvent
from ..persistence.sqlite_cache.cache_maintenance import CacheMaintenance
from ..persistence.sqlite_cache.cache_orchestrator import CacheOrchestrator
from ..workers.load_workers import SourceLoadWorker, ThreadDetailsWorker


class ImportService(QObject):
    source_resolved = Signal(object)
    source_load_started = Signal(str)
    source_load_progress = Signal(int, str)
    source_load_batch = Signal(list)
    source_load_done = Signal(dict)
    source_load_error = Signal(str)

    health_events = Signal(list)

    detail_load_started = Signal(str)
    detail_load_done = Signal(object)
    detail_load_error = Signal(str)

    def __init__(self, cache: CacheStore) -> None:
        super().__init__()
        self._cache = cache
        self._resolver = SourceResolver()
        self._descriptor: SourceDescriptor | None = None
        self._source_worker: SourceLoadWorker | None = None
        self._detail_worker: ThreadDetailsWorker | None = None
        self._active_hot_db_path: Path | None = None
        self._active_blob_db_path: Path | None = None

        self._cache_maintenance = CacheMaintenance(CACHE_ROOT_DIR)

    def start_load(self, source_text: str, parse_chunk_size: int, max_json_fallback_mb: int) -> None:
        self._cancel_workers()
        self._cleanup_descriptor()
        self._cache.clear()
        self._active_hot_db_path = None
        self._active_blob_db_path = None

        try:
            descriptor = self._resolver.resolve(source_text)
        except Exception as exc:
            self.source_load_error.emit(str(exc))
            return

        self._descriptor = descriptor
        self.source_resolved.emit(descriptor)
        self.source_load_started.emit(source_text)

        worker = SourceLoadWorker(
            source_path=descriptor.path,
            source_label=descriptor.source_label,
            warnings=descriptor.warnings,
            parse_chunk_size=parse_chunk_size,
            max_json_fallback_mb=max_json_fallback_mb,
            cache_root=CACHE_ROOT_DIR,
            schema_version=CACHE_SCHEMA_VERSION,
            parser_version=CACHE_PARSER_VERSION,
        )
        self._source_worker = worker

        worker.progress.connect(self.source_load_progress)
        worker.batch.connect(self._on_batch)
        worker.health.connect(self._on_health)
        worker.completed.connect(self._on_load_complete)
        worker.failed.connect(self.source_load_error)
        worker.start()

    def _on_load_complete(self, payload: dict) -> None:
        hot_path = payload.get("hot_db_path")
        blob_path = payload.get("blob_db_path")
        self._active_hot_db_path = Path(hot_path) if hot_path else None
        self._active_blob_db_path = Path(blob_path) if blob_path else None
        self.source_load_done.emit(payload)

    def load_thread_details(self, thread_id: str, max_json_fallback_mb: int) -> None:
        _ = max_json_fallback_mb  # retained for call compatibility with UI settings.

        if not thread_id:
            return

        cached = self._cache.get_details(thread_id)
        if cached is not None:
            self.detail_load_done.emit(cached)
            return

        if self._active_hot_db_path is None or self._active_blob_db_path is None:
            self.detail_load_error.emit("No active cache loaded")
            return

        if self._detail_worker is not None and self._detail_worker.isRunning():
            self._detail_worker.cancel()
            self._detail_worker.wait()

        self.detail_load_started.emit(thread_id)
        worker = ThreadDetailsWorker(
            hot_db_path=self._active_hot_db_path,
            blob_db_path=self._active_blob_db_path,
            thread_id=thread_id,
        )
        self._detail_worker = worker

        def on_loaded(details) -> None:
            self._cache.store_details(details, DETAIL_CACHE_LIMIT)
            self.detail_load_done.emit(details)

        worker.loaded.connect(on_loaded)
        worker.failed.connect(self.detail_load_error)
        worker.start()

    def clear_current_source_cache(self) -> bool:
        descriptor = self._descriptor
        if descriptor is None:
            return False

        orchestrator = CacheOrchestrator(
            cache_root=CACHE_ROOT_DIR,
            schema_version=CACHE_SCHEMA_VERSION,
            parser_version=CACHE_PARSER_VERSION,
        )
        return orchestrator.clear_cache_for_source(descriptor.source_label)

    def clear_all_caches(self) -> None:
        self._cache_maintenance.clear_all()

    def cache_total_size_bytes(self) -> int:
        return self._cache_maintenance.total_cache_size_bytes()

    def _on_batch(self, rows: list) -> None:
        self._cache.add_batch(rows)
        self.source_load_batch.emit(rows)

    def _on_health(self, events: list[HealthEvent]) -> None:
        self._cache.add_health_events(events)
        self.health_events.emit(events)

    def _cancel_workers(self) -> None:
        if self._source_worker is not None and self._source_worker.isRunning():
            self._source_worker.cancel()
            self._source_worker.wait()
        self._source_worker = None

        if self._detail_worker is not None and self._detail_worker.isRunning():
            self._detail_worker.cancel()
            self._detail_worker.wait()
        self._detail_worker = None

    def _cleanup_descriptor(self) -> None:
        if self._descriptor is not None:
            self._descriptor.cleanup()
            self._descriptor = None

    def shutdown(self) -> None:
        self._cancel_workers()
        self._cleanup_descriptor()
