from __future__ import annotations

from pathlib import Path

from .config.defaults import (
    DEFAULT_SOURCE_CANDIDATES,
    THEME_DARK,
)
from .data.cache_store import CacheStore
from .services.import_service import ImportService
from .services.markdown_service import MarkdownService
from .services.query_service import QueryService
from .services.stats_service import StatsService
from .ui.main_window import MainWindow


def _resolve_default_source() -> str:
    for candidate in DEFAULT_SOURCE_CANDIDATES:
        try:
            if Path(candidate).exists():
                return str(candidate)
        except OSError:
            continue
    return str(DEFAULT_SOURCE_CANDIDATES[0]) if DEFAULT_SOURCE_CANDIDATES else ""


def create_window(app) -> MainWindow:
    cache = CacheStore()
    import_service = ImportService(cache)
    query_service = QueryService()
    stats_service = StatsService()
    markdown_service = MarkdownService()

    window = MainWindow(
        app=app,
        cache=cache,
        import_service=import_service,
        query_service=query_service,
        stats_service=stats_service,
        markdown_service=markdown_service,
        default_source=_resolve_default_source(),
        default_theme=THEME_DARK,
    )
    return window
