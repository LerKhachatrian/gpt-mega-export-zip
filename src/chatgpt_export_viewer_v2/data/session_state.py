from __future__ import annotations

import json
from pathlib import Path

SESSION_DIR = Path.home() / ".chatgpt_export_viewer_v2"
SESSION_FILE = SESSION_DIR / "session_state.json"


def load_session_state() -> dict:
    try:
        if not SESSION_FILE.exists():
            return {}
        payload = json.loads(SESSION_FILE.read_text(encoding="utf-8", errors="ignore"))
        if isinstance(payload, dict):
            return payload
    except Exception:
        return {}
    return {}


def save_session_state(state: dict) -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
