from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout, QSplitter, QWidget

from ..components.filter_panel import FilterPanel
from ..components.thread_inspector import ThreadInspector
from ..components.thread_list_view import ThreadListView
from ..components.skeletons import inspector_skeleton_markdown, thread_list_skeleton_rows


class ThreadsPage(QWidget):
    thread_selected = Signal(str)
    filters_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        splitter = QSplitter(self)

        self.filter_panel = FilterPanel(splitter)
        self.list_view = ThreadListView(splitter)
        self.inspector = ThreadInspector(splitter)

        splitter.addWidget(self.filter_panel)
        splitter.addWidget(self.list_view)
        splitter.addWidget(self.inspector)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 2)

        layout.addWidget(splitter)

        self.filter_panel.filters_changed.connect(self.filters_changed.emit)
        self.list_view.thread_selected.connect(self.thread_selected.emit)

    def set_loading(self) -> None:
        self.filter_panel.set_status("Loading")
        self.list_view.set_skeleton(thread_list_skeleton_rows())
        self.inspector.markdown_view.setMarkdown(inspector_skeleton_markdown())

    def set_ready(self) -> None:
        self.filter_panel.set_status("Ready")

    def set_rows(self, rows: list, preserve_thread_id: str | None = None) -> None:
        self.list_view.set_rows(rows, preserve_thread_id=preserve_thread_id)

    def set_coding_threshold(self, threshold: float) -> None:
        self.list_view.set_coding_threshold(threshold)

    def set_number_format_mode(self, mode: str) -> None:
        self.list_view.set_number_format_mode(mode)

    def selected_thread_id(self) -> str | None:
        return self.list_view.selected_thread_id()

    def current_filters(self) -> dict:
        return self.filter_panel.current_filters()

    def restore_filters(
        self,
        query: str,
        shared_only: bool,
        parse_health: str,
        sort_mode: str,
        thread_type: str,
        min_confidence_pct: int,
    ) -> None:
        self.filter_panel.restore_filters(
            query=query,
            shared_only=shared_only,
            parse_health=parse_health,
            sort_mode=sort_mode,
            thread_type=thread_type,
            min_confidence_pct=min_confidence_pct,
        )
