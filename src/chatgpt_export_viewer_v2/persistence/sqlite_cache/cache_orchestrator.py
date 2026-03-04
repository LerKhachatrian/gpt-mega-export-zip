from __future__ import annotations

from pathlib import Path

from ...domain.cache_models import CacheBuildResult, CacheEntry
from .cache_paths import (
    blob_db_path,
    blob_db_tmp_path,
    cache_dir,
    hot_db_path,
    hot_db_tmp_path,
    source_cache_key,
)
from .cache_reader import CacheReader
from .cache_writer import CacheWriter
from .manifest_store import ManifestStore
from .source_fingerprint import build_fingerprint


class CacheOrchestrator:
    def __init__(
        self,
        cache_root: Path,
        schema_version: int,
        parser_version: str,
    ) -> None:
        self._cache_root = cache_root
        self._schema_version = schema_version
        self._parser_version = parser_version
        self._manifest = ManifestStore(cache_root / "manifest.db")

    def ensure_cache(
        self,
        source_path: Path,
        source_label: str,
        parse_chunk_size: int,
        max_json_fallback_mb: int,
        on_batch,
        on_progress,
        on_health,
        is_cancelled,
    ) -> CacheBuildResult:
        cache_key = source_cache_key(source_label)
        hot_path = hot_db_path(self._cache_root, cache_key)
        blob_path = blob_db_path(self._cache_root, cache_key)
        folder = cache_dir(self._cache_root, cache_key)
        folder.mkdir(parents=True, exist_ok=True)

        fingerprint = build_fingerprint(source_path=source_path, source_label=source_label)
        manifest_row = self._manifest.get(cache_key)

        if self._is_cache_valid(manifest_row, fingerprint.source_signature, fingerprint.files_signature, hot_path, blob_path):
            on_progress(2, "Cache hit: loading indexed data")
            reader = CacheReader(hot_db_path=hot_path, blob_db_path=blob_path)
            total_rows = reader.stream_summaries(chunk_size=parse_chunk_size, on_batch=on_batch)
            health = reader.health_events()
            if health:
                on_health(health)
            on_progress(100, f"Cache ready | loaded {total_rows:,} threads")

            entry = CacheEntry(
                cache_key=cache_key,
                source_label=source_label,
                source_signature=fingerprint.source_signature,
                files_signature=fingerprint.files_signature,
                schema_version=self._schema_version,
                parser_version=self._parser_version,
                hot_db_path=hot_path,
                blob_db_path=blob_path,
                total_rows=total_rows,
                built_at=float(manifest_row["built_at"]) if manifest_row else 0.0,
            )
            return CacheBuildResult(cache_entry=entry, cache_built=False)

        on_progress(1, "Cache miss: building cache")
        writer = CacheWriter(
            hot_db_tmp=hot_db_tmp_path(self._cache_root, cache_key),
            blob_db_tmp=blob_db_tmp_path(self._cache_root, cache_key),
        )

        total_rows = writer.build(
            source_path=source_path,
            parse_chunk_size=parse_chunk_size,
            max_json_fallback_mb=max_json_fallback_mb,
            on_batch=on_batch,
            on_progress=on_progress,
            on_health=on_health,
            is_cancelled=is_cancelled,
        )

        if is_cancelled():
            raise RuntimeError("Load cancelled")

        hot_tmp = hot_db_tmp_path(self._cache_root, cache_key)
        blob_tmp = blob_db_tmp_path(self._cache_root, cache_key)

        if hot_path.exists():
            hot_path.unlink()
        if blob_path.exists():
            blob_path.unlink()

        hot_tmp.rename(hot_path)
        blob_tmp.rename(blob_path)

        self._manifest.upsert(
            cache_key=cache_key,
            source_label=source_label,
            source_signature=fingerprint.source_signature,
            files_signature=fingerprint.files_signature,
            schema_version=self._schema_version,
            parser_version=self._parser_version,
            hot_db_path=hot_path,
            blob_db_path=blob_path,
            total_rows=total_rows,
        )

        entry = CacheEntry(
            cache_key=cache_key,
            source_label=source_label,
            source_signature=fingerprint.source_signature,
            files_signature=fingerprint.files_signature,
            schema_version=self._schema_version,
            parser_version=self._parser_version,
            hot_db_path=hot_path,
            blob_db_path=blob_path,
            total_rows=total_rows,
            built_at=0.0,
        )
        on_progress(100, f"Cache built | indexed {total_rows:,} threads")
        return CacheBuildResult(cache_entry=entry, cache_built=True)

    def clear_cache_for_source(self, source_label: str) -> bool:
        cache_key = source_cache_key(source_label)
        folder = cache_dir(self._cache_root, cache_key)
        hot_path = hot_db_path(self._cache_root, cache_key)
        blob_path = blob_db_path(self._cache_root, cache_key)

        if hot_path.exists():
            hot_path.unlink()
        if blob_path.exists():
            blob_path.unlink()

        for tmp in (hot_db_tmp_path(self._cache_root, cache_key), blob_db_tmp_path(self._cache_root, cache_key)):
            if tmp.exists():
                tmp.unlink()

        try:
            if folder.exists() and not any(folder.iterdir()):
                folder.rmdir()
        except OSError:
            pass

        self._manifest.remove(cache_key)
        return True

    def _is_cache_valid(
        self,
        manifest_row: dict | None,
        source_signature: str,
        files_signature: str,
        hot_path: Path,
        blob_path: Path,
    ) -> bool:
        if not manifest_row:
            return False
        if not hot_path.exists() or not blob_path.exists():
            return False
        if int(manifest_row.get("schema_version") or 0) != self._schema_version:
            return False
        if str(manifest_row.get("parser_version") or "") != self._parser_version:
            return False
        if str(manifest_row.get("source_signature") or "") != source_signature:
            return False
        if str(manifest_row.get("files_signature") or "") != files_signature:
            return False
        return True
