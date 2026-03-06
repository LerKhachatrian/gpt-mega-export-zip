from __future__ import annotations

from pathlib import Path

THEME_DARK = "dark"
THEME_LIGHT = "light"


def _windows_to_wsl(path: str) -> Path:
    if not path.startswith("C:"):
        return Path(path)
    windows_body = path[3:].replace("\\", "/").lstrip("/")
    return Path("/mnt/c") / windows_body


DEFAULT_SOURCE_WINDOWS = Path(
    r"C:\Users\Apex University\Downloads\d52893e853ea1f8308bf92d6d2737f514abdbee35bed1188bfd32c6084669acc-2026-02-17-05-23-28-c8329ad9dcf246ecbe1d0048b3218f8d_unzipped"
)
DEFAULT_SOURCE_WSL = _windows_to_wsl(str(DEFAULT_SOURCE_WINDOWS))
DEFAULT_SOURCE_CANDIDATES = [DEFAULT_SOURCE_WINDOWS, DEFAULT_SOURCE_WSL]

PROJECT_ROOT = Path(__file__).resolve().parents[3]
THEME_DARK_PATH = PROJECT_ROOT / "src" / "chatgpt_export_viewer_v2" / "ui" / "styles" / "theme_dark.qss"
THEME_LIGHT_PATH = PROJECT_ROOT / "src" / "chatgpt_export_viewer_v2" / "ui" / "styles" / "theme_light.qss"

PARSE_CHUNK_SIZE = 250
THREAD_LIST_PAGE_SIZE = 250
DETAIL_CACHE_LIMIT = 200
MAX_JSON_FALLBACK_MB = 128
DEFAULT_CODING_THRESHOLD = 0.50
DEFAULT_MIN_CODING_CONFIDENCE = 0.00

CACHE_SCHEMA_VERSION = 3
CACHE_PARSER_VERSION = "2.3"
CACHE_ROOT_DIR = Path.home() / ".chatgpt_export_viewer_v2" / "sqlite_cache"
