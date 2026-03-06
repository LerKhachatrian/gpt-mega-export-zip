from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...config.defaults import THREAD_LIST_PAGE_SIZE
from ...domain.models import ThreadSummary
from ...services.number_format_service import NUMBER_FORMAT_COMPACT, format_quantity, normalize_number_format_mode


class ThreadListView(QWidget):
    thread_selected = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._rows: list[ThreadSummary] = []
        self._rendered_count = 0
        self._page_size = THREAD_LIST_PAGE_SIZE
        self._coding_threshold = 0.50
        self._number_format_mode = NUMBER_FORMAT_COMPACT

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        head = QWidget(self)
        head_layout = QHBoxLayout(head)
        head_layout.setContentsMargins(0, 0, 0, 0)
        self.count_label = QLabel("0 results", head)
        self.count_label.setObjectName("mutedLabel")
        self.load_more_btn = QPushButton("Load more", head)
        self.load_more_btn.clicked.connect(self.load_more)
        head_layout.addWidget(self.count_label)
        head_layout.addStretch(1)
        head_layout.addWidget(self.load_more_btn)

        self.list_widget = QListWidget(self)
        self.list_widget.currentItemChanged.connect(self._on_current_changed)
        self.list_widget.verticalScrollBar().valueChanged.connect(self._on_scroll)

        layout.addWidget(head)
        layout.addWidget(self.list_widget, 1)

        self._refresh_controls()

    def set_skeleton(self, rows: list[str]) -> None:
        self._rows = []
        self._rendered_count = 0
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for text in rows:
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, "")
            item.setForeground(Qt.GlobalColor.gray)
            self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)
        self.count_label.setText("Loading...")
        self.load_more_btn.setVisible(False)

    def set_rows(self, rows: list[ThreadSummary], preserve_thread_id: str | None = None) -> None:
        self._rows = rows
        self._rendered_count = 0

        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        self.list_widget.blockSignals(False)

        self.load_more()

        if preserve_thread_id:
            for index in range(self.list_widget.count()):
                item = self.list_widget.item(index)
                if item.data(Qt.ItemDataRole.UserRole) == preserve_thread_id:
                    self.list_widget.setCurrentItem(item)
                    break

        self._refresh_controls()

    def load_more(self) -> None:
        if self._rendered_count >= len(self._rows):
            self._refresh_controls()
            return

        end = min(self._rendered_count + self._page_size, len(self._rows))
        self.list_widget.blockSignals(True)
        for row in self._rows[self._rendered_count : end]:
            self.list_widget.addItem(self._build_item(row))
        self.list_widget.blockSignals(False)

        self._rendered_count = end
        self._refresh_controls()

    def set_coding_threshold(self, threshold: float) -> None:
        self._coding_threshold = min(1.0, max(0.0, float(threshold)))

    def set_number_format_mode(self, mode: str) -> None:
        self._number_format_mode = normalize_number_format_mode(mode)

    def _build_item(self, row: ThreadSummary) -> QListWidgetItem:
        shared = " [shared]" if row.is_shared else ""
        health = " [partial]" if row.parse_health != "ok" else ""
        has_classification = (row.code_chars + row.non_code_chars) > 0
        is_primary = has_classification and row.code_ratio >= self._coding_threshold
        label = "coding" if is_primary else "non-coding"
        if not has_classification:
            label = "analyzing"
        code_ratio_pct = row.code_ratio * 100.0
        confidence_pct = row.coding_confidence * 100.0
        line = (
            f"{row.title}{shared}{health}\n"
            f"{row.snippet}\n"
            f"{format_quantity(row.total_messages, mode=self._number_format_mode)} msgs | "
            f"{format_quantity(row.words, mode=self._number_format_mode)} words | "
            f"{format_quantity(row.tokens_o200k, mode=self._number_format_mode)} tok(o200k) | "
            f"{label} {code_ratio_pct:.0f}% | conf {confidence_pct:.0f}%"
        )
        item = QListWidgetItem(line)
        item.setData(Qt.ItemDataRole.UserRole, row.thread_id)
        item.setToolTip(row.thread_id)
        return item

    def _refresh_controls(self) -> None:
        total = len(self._rows)
        mode = self._number_format_mode
        self.count_label.setText(
            f"{format_quantity(total, mode=mode)} results | showing {format_quantity(self._rendered_count, mode=mode)}"
        )
        self.load_more_btn.setVisible(self._rendered_count < total)

    def _on_current_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is None:
            return
        thread_id = current.data(Qt.ItemDataRole.UserRole)
        if thread_id:
            self.thread_selected.emit(thread_id)

    def _on_scroll(self, value: int) -> None:
        bar = self.list_widget.verticalScrollBar()
        if bar.maximum() <= 0:
            return
        if value >= int(bar.maximum() * 0.9):
            self.load_more()

    def selected_thread_id(self) -> str | None:
        item = self.list_widget.currentItem()
        if item is None:
            return None
        thread_id = item.data(Qt.ItemDataRole.UserRole)
        return thread_id if thread_id else None
