from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QProcess, QTimer
from PySide6.QtGui import QKeySequence, QMouseEvent, QShortcut
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMenu,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..config.defaults import (
    DEFAULT_CODING_THRESHOLD,
    DEFAULT_MIN_CODING_CONFIDENCE,
    MAX_JSON_FALLBACK_MB,
    PARSE_CHUNK_SIZE,
    THEME_DARK,
    THEME_DARK_PATH,
    THEME_LIGHT,
    THEME_LIGHT_PATH,
)
from ..config.state import RuntimeState
from ..data.cache_store import CacheStore
from ..data.session_state import load_session_state, save_session_state
from ..domain.enums import LoadState, ThreadTypeFilter
from ..domain.models import HealthEvent
from ..services.import_service import ImportService
from ..services.markdown_service import MarkdownService
from ..services.number_format_service import (
    NUMBER_FORMAT_COMPACT,
    format_quantity,
    normalize_number_format_mode,
)
from ..services.query_service import QueryService
from ..services.stats_service import StatsService
from .pages.health_page import HealthPage
from .pages.overview_page import OverviewPage
from .pages.settings_page import SettingsPage
from .pages.stats_page import StatsPage
from .pages.threads_page import ThreadsPage


class MainWindow(QMainWindow):
    PAGE_OVERVIEW = 0
    PAGE_THREADS = 1
    PAGE_STATS = 2
    PAGE_HEALTH = 3
    PAGE_SETTINGS = 4
    HOT_CORNER_SIZE = 50

    def __init__(
        self,
        app,
        cache: CacheStore,
        import_service: ImportService,
        query_service: QueryService,
        stats_service: StatsService,
        markdown_service: MarkdownService,
        default_source: str,
        default_theme: str,
    ) -> None:
        super().__init__()
        self.setWindowTitle("GPT Mega Export (.zip)")
        self.resize(1700, 980)

        self._app = app
        self._cache = cache
        self._import_service = import_service
        self._query_service = query_service
        self._stats_service = stats_service
        self._markdown_service = markdown_service

        self._state = RuntimeState(
            source_path=default_source,
            theme=default_theme,
            load_state=LoadState.IDLE,
        )

        self._parse_chunk_size = PARSE_CHUNK_SIZE
        self._max_json_fallback_mb = MAX_JSON_FALLBACK_MB
        self._coding_threshold = DEFAULT_CODING_THRESHOLD
        self._min_coding_confidence = DEFAULT_MIN_CODING_CONFIDENCE
        self._number_format_mode = NUMBER_FORMAT_COMPACT

        self._rows_indexed = 0
        self._health_event_count = 0
        self._last_progress_text = "Ready"

        self._build_ui()
        self._wire_signals()

        restored = self._restore_session_state()
        if not restored:
            self._apply_theme(default_theme)
            self.source_input.setText(default_source)
            self._apply_number_format_mode(NUMBER_FORMAT_COMPACT)

        source = self.source_input.text().strip()
        if source:
            self.start_load()

    def _build_ui(self) -> None:
        root = QWidget(self)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root)

        self.sidebar = QListWidget(root)
        self.sidebar.setFixedWidth(220)
        self.sidebar.addItems(["Overview", "Threads", "Stats", "Health", "Settings"])
        self.sidebar.setCurrentRow(self.PAGE_THREADS)

        right = QWidget(root)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(14, 12, 14, 10)
        right_layout.setSpacing(10)

        top = QWidget(right)
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(0, 0, 0, 0)

        self.source_input = QLineEdit(top)
        self.source_input.setPlaceholderText("Select ChatGPT export folder or zip")
        self.browse_btn = QPushButton("Browse", top)
        self.load_btn = QPushButton("Load", top)
        self.reload_btn = QPushButton("Reload", top)
        self.quick_search = QLineEdit(top)
        self.quick_search.setPlaceholderText("Quick search (Ctrl+K)")

        top_layout.addWidget(QLabel("Source", top))
        top_layout.addWidget(self.source_input, 1)
        top_layout.addWidget(self.browse_btn)
        top_layout.addWidget(self.load_btn)
        top_layout.addWidget(self.reload_btn)
        top_layout.addSpacing(10)
        top_layout.addWidget(QLabel("Search", top))
        top_layout.addWidget(self.quick_search, 1)

        self.pages = QStackedWidget(right)
        self.overview_page = OverviewPage(self.pages)
        self.threads_page = ThreadsPage(self.pages)
        self.stats_page = StatsPage(self.pages)
        self.health_page = HealthPage(self.pages)
        self.settings_page = SettingsPage(self.pages)

        self.pages.addWidget(self.overview_page)
        self.pages.addWidget(self.threads_page)
        self.pages.addWidget(self.stats_page)
        self.pages.addWidget(self.health_page)
        self.pages.addWidget(self.settings_page)

        bottom = QWidget(right)
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        self.progress = QProgressBar(bottom)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%")

        self.status_label = QLabel("Ready", bottom)
        self.status_label.setObjectName("mutedLabel")

        self.telemetry_label = QLabel("rows: 0 | health: 0 | cache: 0.0 MB", bottom)
        self.telemetry_label.setObjectName("mutedLabel")
        self.telemetry_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        bottom_layout.addWidget(self.progress, 2)
        bottom_layout.addWidget(self.status_label, 3)
        bottom_layout.addWidget(self.telemetry_label, 1)

        right_layout.addWidget(top)
        right_layout.addWidget(self.pages, 1)
        right_layout.addWidget(bottom)

        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(right, 1)

        self._query_timer = QTimer(self)
        self._query_timer.setInterval(120)
        self._query_timer.setSingleShot(True)

        self._stats_refresh_timer = QTimer(self)
        self._stats_refresh_timer.setInterval(220)
        self._stats_refresh_timer.setSingleShot(True)

    def _wire_signals(self) -> None:
        self.sidebar.currentRowChanged.connect(self.pages.setCurrentIndex)

        self.browse_btn.clicked.connect(self.choose_source)
        self.load_btn.clicked.connect(self.start_load)
        self.reload_btn.clicked.connect(self.start_load)

        self.quick_search.textChanged.connect(self._on_quick_search)
        self.threads_page.filters_changed.connect(self.schedule_query)
        self.threads_page.thread_selected.connect(self.load_selected_thread)

        self.settings_page.settings_changed.connect(self._on_settings_changed)
        self.settings_page.cache_action_requested.connect(self._on_cache_action)

        self._query_timer.timeout.connect(self.apply_query)
        self._stats_refresh_timer.timeout.connect(self._refresh_stats)

        self._import_service.source_resolved.connect(self._on_source_resolved)
        self._import_service.source_load_started.connect(self._on_load_started)
        self._import_service.source_load_progress.connect(self._on_load_progress)
        self._import_service.source_load_batch.connect(self._on_load_batch)
        self._import_service.source_load_done.connect(self._on_load_done)
        self._import_service.source_load_error.connect(self._on_load_error)
        self._import_service.health_events.connect(self._on_health_events)

        self._import_service.detail_load_started.connect(self._on_detail_started)
        self._import_service.detail_load_done.connect(self._on_detail_done)
        self._import_service.detail_load_error.connect(self._on_detail_error)

        QShortcut(QKeySequence("Ctrl+K"), self, activated=self.quick_search.setFocus)
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.start_load)
        QShortcut(QKeySequence("Ctrl+Shift+R"), self, activated=self._restart_application)
        QShortcut(QKeySequence("Ctrl+1"), self, activated=lambda: self.sidebar.setCurrentRow(self.PAGE_OVERVIEW))
        QShortcut(QKeySequence("Ctrl+2"), self, activated=lambda: self.sidebar.setCurrentRow(self.PAGE_THREADS))

    def choose_source(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select export folder", str(Path.home()))
        if directory:
            self.source_input.setText(directory)
            return

        path, _ = QFileDialog.getOpenFileName(self, "Select export zip", str(Path.home()), "Zip files (*.zip)")
        if path:
            self.source_input.setText(path)

    def start_load(self) -> None:
        source = self.source_input.text().strip()
        if not source:
            self._set_status("Source is empty")
            return

        self._state.load_state = LoadState.LOADING
        self._state.source_path = source
        self._rows_indexed = 0
        self._health_event_count = 0
        self._last_progress_text = "Starting load..."
        self._stats_refresh_timer.stop()

        self.progress.setRange(0, 0)
        self._refresh_telemetry()
        self._set_status("Starting load...")

        self.health_page.clear_events()
        self.overview_page.set_source(source)
        self.overview_page.set_loading()
        self.stats_page.set_loading()
        self.threads_page.set_loading()
        self.threads_page.inspector.set_placeholder("Parsing or reading cache")

        self._import_service.start_load(
            source_text=source,
            parse_chunk_size=self._parse_chunk_size,
            max_json_fallback_mb=self._max_json_fallback_mb,
        )

    def _on_source_resolved(self, descriptor) -> None:
        self.overview_page.set_source(str(descriptor.source_label))

    def _on_load_started(self, source: str) -> None:
        self._set_status(f"Loading {source}")
        self.threads_page.filter_panel.set_status("Loading")

    def _on_load_progress(self, percent: int, message: str) -> None:
        self._last_progress_text = message
        self.progress.setRange(0, 100)
        self.progress.setValue(percent)
        self._set_status(message)

    def _on_load_batch(self, rows: list) -> None:
        _ = rows  # Batched rows are already merged into cache store by ImportService.
        self._rows_indexed = self._cache.count()
        self._refresh_telemetry()
        self.threads_page.filter_panel.set_status(
            f"Loading ({format_quantity(self._rows_indexed, mode=self._number_format_mode)} indexed)"
        )
        self.schedule_query()

        # Throttle expensive whole-dataset stats recompute during heavy batch streams.
        if not self._stats_refresh_timer.isActive():
            self._stats_refresh_timer.start()

    def _on_load_done(self, payload: dict) -> None:
        self._state.load_state = LoadState.READY
        self.progress.setRange(0, 100)
        self.progress.setValue(100)

        total_rows = int(payload.get("total_rows", 0) or 0)
        cache_built = bool(payload.get("cache_built", False))

        self._rows_indexed = total_rows
        self._refresh_telemetry()
        total_rows_text = format_quantity(total_rows, mode=self._number_format_mode)

        if cache_built:
            self._set_status(f"Cache built and loaded: {total_rows_text} threads")
        else:
            self._set_status(f"Loaded from cache: {total_rows_text} threads")

        self.threads_page.set_ready()
        self._stats_refresh_timer.stop()
        self.apply_query()
        self._refresh_stats()

        if self.pages.currentIndex() != self.PAGE_THREADS:
            self.pages.setCurrentIndex(self.PAGE_THREADS)
            self.sidebar.setCurrentRow(self.PAGE_THREADS)

    def _on_load_error(self, message: str) -> None:
        self._state.load_state = LoadState.ERROR
        self._stats_refresh_timer.stop()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self._set_status(f"Load failed: {message}")
        event = HealthEvent(level="error", code="load_failed", message=message)
        self._health_event_count += 1
        self._refresh_telemetry()
        self.health_page.add_events([event])

    def _on_health_events(self, events: list[HealthEvent]) -> None:
        self._health_event_count += len(events)
        self._refresh_telemetry()
        self.health_page.add_events(events)
        self._refresh_stats()

    def _on_detail_started(self, thread_id: str) -> None:
        self.threads_page.inspector.set_loading(thread_id)

    def _on_detail_done(self, details) -> None:
        self.threads_page.inspector.set_details(details, self._markdown_service)

    def _on_detail_error(self, message: str) -> None:
        self.threads_page.inspector.set_error(message)
        self._health_event_count += 1
        self._refresh_telemetry()
        self.health_page.add_events([HealthEvent(level="error", code="detail_failed", message=message)])

    def _on_quick_search(self, value: str) -> None:
        self.threads_page.filter_panel.set_search_text(value)
        self.schedule_query()

    def _on_settings_changed(self, settings: dict) -> None:
        theme = settings.get("theme") or THEME_DARK
        self._parse_chunk_size = int(settings.get("parse_chunk_size") or PARSE_CHUNK_SIZE)
        self._max_json_fallback_mb = int(settings.get("max_json_fallback_mb") or MAX_JSON_FALLBACK_MB)
        coding_threshold_pct = int(settings.get("coding_threshold_pct") or int(DEFAULT_CODING_THRESHOLD * 100))
        self._coding_threshold = max(0.0, min(1.0, coding_threshold_pct / 100.0))
        self._apply_number_format_mode(str(settings.get("number_format_mode") or NUMBER_FORMAT_COMPACT))
        self._apply_theme(theme)
        self.apply_query()
        self._refresh_stats()

    def _on_cache_action(self, action: str) -> None:
        if action == "clear_all":
            self._import_service.clear_all_caches()
            self._set_status("All caches cleared")
            self._refresh_telemetry()
            return

        if action == "clear_current":
            if self._import_service.clear_current_source_cache():
                self._set_status("Current source cache cleared")
            else:
                self._set_status("No current source cache to clear")
            self._refresh_telemetry()
            return

        if action == "rebuild_current":
            if self._import_service.clear_current_source_cache():
                self._set_status("Current source cache cleared, rebuilding...")
            self.start_load()

    def schedule_query(self) -> None:
        self._query_timer.start()

    def apply_query(self) -> None:
        filters = self.threads_page.current_filters()
        current_thread = self.threads_page.selected_thread_id()

        rows = self._cache.snapshot()
        visible = self._query_service.apply(
            rows=rows,
            query=filters["query"],
            shared_only=filters["shared_only"],
            parse_health=filters["parse_health"],
            sort_mode=filters["sort_mode"],
            thread_type=filters.get("thread_type", ThreadTypeFilter.ALL),
            coding_threshold=self._coding_threshold,
            min_coding_confidence=filters.get("min_coding_confidence", self._min_coding_confidence),
        )

        self.threads_page.set_coding_threshold(self._coding_threshold)
        self.threads_page.set_rows(visible, preserve_thread_id=current_thread)

    def load_selected_thread(self, thread_id: str) -> None:
        self._import_service.load_thread_details(thread_id, max_json_fallback_mb=self._max_json_fallback_mb)

    def _refresh_stats(self) -> None:
        rows = self._cache.snapshot()
        health = self._cache.health_events()
        stats = self._stats_service.global_stats(rows, health, coding_threshold=self._coding_threshold)
        self.overview_page.update_stats(stats)
        self.stats_page.update_stats(stats, self._stats_service.top_threads(rows, limit=30))

    def _apply_theme(self, theme: str) -> None:
        if theme == THEME_LIGHT:
            qss_path = THEME_LIGHT_PATH
        else:
            qss_path = THEME_DARK_PATH
            theme = THEME_DARK

        self._state.theme = theme
        self.settings_page.set_theme(theme)

        if qss_path.exists():
            self._app.setStyleSheet(qss_path.read_text(encoding="utf-8", errors="ignore"))

    def _set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def _refresh_telemetry(self) -> None:
        cache_size_mb = self._import_service.cache_total_size_bytes() / (1024 * 1024)
        self.telemetry_label.setText(
            f"rows: {format_quantity(self._rows_indexed, mode=self._number_format_mode)} | "
            f"health: {format_quantity(self._health_event_count, mode=self._number_format_mode)} | "
            f"cache: {cache_size_mb:,.1f} MB"
        )

    def _apply_number_format_mode(self, mode: str) -> None:
        self._number_format_mode = normalize_number_format_mode(mode)
        self._state.number_format_mode = self._number_format_mode
        self.settings_page.set_number_format_mode(self._number_format_mode)
        self.overview_page.set_number_format_mode(self._number_format_mode)
        self.stats_page.set_number_format_mode(self._number_format_mode)
        self.threads_page.set_number_format_mode(self._number_format_mode)
        self._refresh_telemetry()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.RightButton and self._is_hot_corner(event):
            self._show_restart_menu(event)
            event.accept()
            return
        super().mousePressEvent(event)

    def _is_hot_corner(self, event: QMouseEvent) -> bool:
        point = event.position().toPoint()
        return point.x() >= (self.width() - self.HOT_CORNER_SIZE) and point.y() <= self.HOT_CORNER_SIZE

    def _show_restart_menu(self, event: QMouseEvent) -> None:
        menu = QMenu(self)
        restart_action = menu.addAction("Restart")
        chosen = menu.exec(event.globalPosition().toPoint())
        if chosen == restart_action:
            self._restart_application()

    def _collect_session_state(self) -> dict:
        filters = self.threads_page.current_filters()
        return {
            "source_path": self.source_input.text().strip(),
            "sidebar_index": int(self.sidebar.currentRow()),
            "quick_search": self.quick_search.text(),
            "theme": self._state.theme,
            "parse_chunk_size": int(self._parse_chunk_size),
            "max_json_fallback_mb": int(self._max_json_fallback_mb),
            "coding_threshold_pct": int(round(self._coding_threshold * 100)),
            "number_format_mode": self._number_format_mode,
            "filter_query": filters.get("query", ""),
            "filter_shared_only": bool(filters.get("shared_only", False)),
            "filter_parse_health": filters.get("parse_health", "all"),
            "filter_sort_mode": getattr(filters.get("sort_mode"), "value", "updated"),
            "filter_thread_type": getattr(filters.get("thread_type"), "value", ThreadTypeFilter.ALL.value),
            "filter_min_coding_confidence_pct": int(round(float(filters.get("min_coding_confidence", 0.0)) * 100)),
        }

    def _restore_session_state(self) -> bool:
        payload = load_session_state()
        if not payload:
            return False

        self._apply_theme(str(payload.get("theme") or THEME_DARK))

        source_path = str(payload.get("source_path") or "")
        self.source_input.setText(source_path)

        sidebar_index = int(payload.get("sidebar_index", self.PAGE_THREADS))
        if 0 <= sidebar_index < self.sidebar.count():
            self.sidebar.setCurrentRow(sidebar_index)

        self._parse_chunk_size = int(payload.get("parse_chunk_size") or PARSE_CHUNK_SIZE)
        self._max_json_fallback_mb = int(payload.get("max_json_fallback_mb") or MAX_JSON_FALLBACK_MB)
        self._apply_number_format_mode(str(payload.get("number_format_mode") or NUMBER_FORMAT_COMPACT))
        self._coding_threshold = max(
            0.0,
            min(
                1.0,
                int(payload.get("coding_threshold_pct") or int(DEFAULT_CODING_THRESHOLD * 100)) / 100.0,
            ),
        )
        self.settings_page.set_parse_chunk_size(self._parse_chunk_size)
        self.settings_page.set_max_json_fallback_mb(self._max_json_fallback_mb)
        self.settings_page.set_coding_threshold_pct(int(round(self._coding_threshold * 100)))

        filter_query = str(payload.get("filter_query") or payload.get("quick_search") or "")
        filter_shared_only = bool(payload.get("filter_shared_only", False))
        filter_parse_health = str(payload.get("filter_parse_health") or "all")
        filter_sort_mode = str(payload.get("filter_sort_mode") or "updated")
        filter_thread_type = str(payload.get("filter_thread_type") or ThreadTypeFilter.ALL.value)
        filter_min_coding_confidence_pct = int(payload.get("filter_min_coding_confidence_pct") or 0)
        self._min_coding_confidence = max(0.0, min(1.0, filter_min_coding_confidence_pct / 100.0))

        self.quick_search.setText(filter_query)
        self.threads_page.restore_filters(
            query=filter_query,
            shared_only=filter_shared_only,
            parse_health=filter_parse_health,
            sort_mode=filter_sort_mode,
            thread_type=filter_thread_type,
            min_confidence_pct=filter_min_coding_confidence_pct,
        )
        return True

    def _restart_application(self) -> None:
        session = self._collect_session_state()
        save_session_state(session)

        project_root = Path(__file__).resolve().parents[3]
        main_script = project_root / "main.py"

        started = QProcess.startDetached(sys.executable, [str(main_script)], str(project_root))
        if not started:
            self._set_status("Restart failed: unable to launch new instance")
            self.health_page.add_events([
                HealthEvent(level="error", code="restart_failed", message="Failed to launch detached process")
            ])
            return

        self._set_status("Restarting...")
        QTimer.singleShot(120, self.close)

    def closeEvent(self, event) -> None:  # pragma: no cover
        try:
            save_session_state(self._collect_session_state())
        except Exception:
            pass

        self._import_service.shutdown()
        super().closeEvent(event)
