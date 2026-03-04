from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ...domain.cache_models import SourceFingerprint


def _file_signature(path: Path) -> dict:
    stat = path.stat()
    return {
        "name": path.name,
        "size": int(stat.st_size),
        "mtime_ns": int(stat.st_mtime_ns),
    }


def build_fingerprint(source_path: Path, source_label: str) -> SourceFingerprint:
    files: list[dict] = []
    for name in ("conversations.json", "shared_conversations.json", "user.json"):
        target = source_path / name
        if target.exists() and target.is_file():
            files.append(_file_signature(target))

    files.sort(key=lambda row: row["name"])

    base_payload = {
        "source_label": source_label,
        "source_path": str(source_path),
        "files": files,
    }

    source_signature = hashlib.sha256(
        json.dumps(base_payload, sort_keys=True, ensure_ascii=False).encode("utf-8", errors="ignore")
    ).hexdigest()

    files_signature = hashlib.sha256(
        json.dumps(files, sort_keys=True, ensure_ascii=False).encode("utf-8", errors="ignore")
    ).hexdigest()

    return SourceFingerprint(source_signature=source_signature, files_signature=files_signature)
