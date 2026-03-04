from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class SourceFingerprint:
    source_signature: str
    files_signature: str


@dataclass
class CacheEntry:
    cache_key: str
    source_label: str
    source_signature: str
    files_signature: str
    schema_version: int
    parser_version: str
    hot_db_path: Path
    blob_db_path: Path
    total_rows: int
    built_at: float


@dataclass
class CacheBuildResult:
    cache_entry: CacheEntry
    cache_built: bool
