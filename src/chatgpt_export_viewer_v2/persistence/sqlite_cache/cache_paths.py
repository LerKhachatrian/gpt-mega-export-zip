from __future__ import annotations

import hashlib
from pathlib import Path


def source_cache_key(source_label: str) -> str:
    digest = hashlib.sha256(source_label.encode("utf-8", errors="ignore")).hexdigest()
    return digest[:24]


def cache_dir(cache_root: Path, cache_key: str) -> Path:
    return cache_root / "sources" / cache_key


def hot_db_path(cache_root: Path, cache_key: str) -> Path:
    return cache_dir(cache_root, cache_key) / "hot.db"


def blob_db_path(cache_root: Path, cache_key: str) -> Path:
    return cache_dir(cache_root, cache_key) / "blob.db"


def hot_db_tmp_path(cache_root: Path, cache_key: str) -> Path:
    return cache_dir(cache_root, cache_key) / "hot.tmp.db"


def blob_db_tmp_path(cache_root: Path, cache_key: str) -> Path:
    return cache_dir(cache_root, cache_key) / "blob.tmp.db"
