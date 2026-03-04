from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Iterator

from ..domain.models import ThreadDetails, ThreadSummary
from .normalizer import build_details, build_summary

try:
    import ijson
except Exception:  # pragma: no cover
    ijson = None


def _iter_thread_objects(path: Path, max_json_fallback_mb: int, is_cancelled: Callable[[], bool] | None) -> Iterator[dict]:
    if ijson is not None:
        with path.open("rb") as fp:
            for item in ijson.items(fp, "item"):
                if is_cancelled and is_cancelled():
                    return
                if isinstance(item, dict):
                    yield item
        return

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > max_json_fallback_mb:
        raise RuntimeError("ijson is required for large exports. Install with: pip install ijson")

    payload = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    for item in payload:
        if is_cancelled and is_cancelled():
            return
        if isinstance(item, dict):
            yield item


def iter_thread_objects_with_progress(
    file_path: Path,
    max_json_fallback_mb: int,
    is_cancelled: Callable[[], bool] | None,
):
    if ijson is not None:
        total_bytes = max(file_path.stat().st_size, 1)
        with file_path.open("rb") as fp:
            count = 0
            for obj in ijson.items(fp, "item"):
                if is_cancelled and is_cancelled():
                    return
                if not isinstance(obj, dict):
                    continue
                count += 1
                pct = min(int((fp.tell() / total_bytes) * 100), 99)
                note = f"Scanning {file_path.name}"
                yield obj, pct, note
        return

    size_mb = file_path.stat().st_size / (1024 * 1024)
    if size_mb > max_json_fallback_mb:
        raise RuntimeError("ijson is required for large exports. Install with: pip install ijson")

    payload = json.loads(file_path.read_text(encoding="utf-8", errors="ignore"))
    total_items = max(len(payload), 1)

    for index, obj in enumerate(payload, start=1):
        if is_cancelled and is_cancelled():
            return
        if not isinstance(obj, dict):
            continue
        pct = min(int((index / total_items) * 100), 99)
        note = f"Scanning {file_path.name}"
        yield obj, pct, note


def iter_summaries(
    file_path: Path,
    is_shared: bool,
    chunk_size: int,
    max_json_fallback_mb: int,
    on_batch: Callable[[list[ThreadSummary]], None] | None = None,
    on_progress: Callable[[int, str], None] | None = None,
    is_cancelled: Callable[[], bool] | None = None,
) -> int:
    count = 0
    chunk: list[ThreadSummary] = []

    for obj, pct, _note in iter_thread_objects_with_progress(
        file_path=file_path,
        max_json_fallback_mb=max_json_fallback_mb,
        is_cancelled=is_cancelled,
    ):
        summary = build_summary(obj, source_file=str(file_path), is_shared=is_shared)
        chunk.append(summary)
        count += 1

        if on_progress and (count == 1 or count % 25 == 0):
            on_progress(pct, f"Scanning {file_path.name} | indexed {count:,} threads")

        if len(chunk) >= chunk_size:
            if on_batch:
                on_batch(chunk)
            chunk = []

    if chunk and on_batch:
        on_batch(chunk)

    if on_progress:
        on_progress(100, f"Parsed {file_path.name} | indexed {count:,} threads")

    return count


def load_thread_details_by_id(
    file_path: Path,
    thread_id: str,
    is_shared: bool,
    max_json_fallback_mb: int,
    is_cancelled: Callable[[], bool] | None = None,
) -> ThreadDetails | None:
    for obj in _iter_thread_objects(file_path, max_json_fallback_mb=max_json_fallback_mb, is_cancelled=is_cancelled):
        candidate = str(obj.get("id") or obj.get("conversation_id") or "")
        if candidate == thread_id:
            return build_details(obj, source_file=str(file_path), is_shared=is_shared)
    return None
