from __future__ import annotations

import shutil
from pathlib import Path

from .manifest_store import ManifestStore


class CacheMaintenance:
    def __init__(self, cache_root: Path) -> None:
        self._cache_root = cache_root
        self._manifest = ManifestStore(cache_root / "manifest.db")

    def clear_all(self) -> None:
        sources_dir = self._cache_root / "sources"
        if sources_dir.exists():
            shutil.rmtree(sources_dir, ignore_errors=True)
        if (self._cache_root / "manifest.db").exists():
            (self._cache_root / "manifest.db").unlink()

    def total_cache_size_bytes(self) -> int:
        total = 0
        if not self._cache_root.exists():
            return total
        for path in self._cache_root.rglob("*"):
            if path.is_file():
                total += path.stat().st_size
        return total

    def list_entries(self) -> list[dict]:
        return self._manifest.list_entries()
