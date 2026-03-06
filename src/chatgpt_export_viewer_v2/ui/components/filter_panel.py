from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QWidget,
)

from ...domain.enums import SortMode, ThreadTypeFilter


class FilterPanel(QWidget):
    filters_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = QFormLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search title, snippet, or thread id")

        self.sort_combo = QComboBox(self)
        self.sort_combo.addItem("Updated", SortMode.UPDATED)
        self.sort_combo.addItem("Created", SortMode.CREATED)
        self.sort_combo.addItem("Messages", SortMode.MESSAGES)
        self.sort_combo.addItem("Words", SortMode.WORDS)
        self.sort_combo.addItem("Tokens (o200k)", SortMode.TOKENS)
        self.sort_combo.addItem("Code Ratio", SortMode.CODE_RATIO)
        self.sort_combo.addItem("Coding Confidence", SortMode.CODING_CONFIDENCE)
        self.sort_combo.addItem("Title", SortMode.TITLE)

        self.shared_only = QCheckBox("Shared threads only", self)

        self.parse_health = QComboBox(self)
        self.parse_health.addItem("All", "all")
        self.parse_health.addItem("Healthy", "ok")
        self.parse_health.addItem("Partial", "partial")

        self.thread_type = QComboBox(self)
        self.thread_type.addItem("All", ThreadTypeFilter.ALL)
        self.thread_type.addItem("Primarily Coding", ThreadTypeFilter.PRIMARY_CODING)
        self.thread_type.addItem("Not Primarily Coding", ThreadTypeFilter.NON_CODING)

        self.min_confidence = QSpinBox(self)
        self.min_confidence.setRange(0, 100)
        self.min_confidence.setSingleStep(5)
        self.min_confidence.setSuffix("%")

        self.active_label = QLabel("Ready", self)
        self.active_label.setObjectName("mutedLabel")

        layout.addRow("Search", self.search_input)
        layout.addRow("Sort", self.sort_combo)
        layout.addRow("Scope", self.shared_only)
        layout.addRow("Health", self.parse_health)
        layout.addRow("Thread Type", self.thread_type)
        layout.addRow("Min Confidence", self.min_confidence)
        layout.addRow("Status", self.active_label)

        self.search_input.textChanged.connect(self.filters_changed.emit)
        self.sort_combo.currentIndexChanged.connect(self.filters_changed.emit)
        self.shared_only.toggled.connect(self.filters_changed.emit)
        self.parse_health.currentIndexChanged.connect(self.filters_changed.emit)
        self.thread_type.currentIndexChanged.connect(self.filters_changed.emit)
        self.min_confidence.valueChanged.connect(self.filters_changed.emit)

    def current_filters(self) -> dict:
        sort_mode = self.sort_combo.currentData()
        if sort_mode is None:
            sort_mode = SortMode.UPDATED
        return {
            "query": self.search_input.text(),
            "shared_only": self.shared_only.isChecked(),
            "parse_health": self.parse_health.currentData() or "all",
            "sort_mode": sort_mode,
            "thread_type": self.thread_type.currentData() or ThreadTypeFilter.ALL,
            "min_coding_confidence": self.min_confidence.value() / 100.0,
        }

    def set_search_text(self, value: str) -> None:
        self.search_input.setText(value)

    def set_shared_only(self, value: bool) -> None:
        self.shared_only.setChecked(bool(value))

    def set_parse_health(self, value: str) -> None:
        for index in range(self.parse_health.count()):
            if self.parse_health.itemData(index) == value:
                self.parse_health.setCurrentIndex(index)
                return

    def set_sort_mode(self, value: str) -> None:
        for index in range(self.sort_combo.count()):
            data = self.sort_combo.itemData(index)
            if getattr(data, "value", data) == value:
                self.sort_combo.setCurrentIndex(index)
                return

    def set_thread_type(self, value: str) -> None:
        for index in range(self.thread_type.count()):
            data = self.thread_type.itemData(index)
            if getattr(data, "value", data) == value:
                self.thread_type.setCurrentIndex(index)
                return

    def set_min_confidence_pct(self, value: int) -> None:
        self.min_confidence.setValue(max(0, min(100, int(value))))

    def restore_filters(
        self,
        query: str,
        shared_only: bool,
        parse_health: str,
        sort_mode: str,
        thread_type: str,
        min_confidence_pct: int,
    ) -> None:
        widgets = [self.search_input, self.shared_only, self.parse_health, self.sort_combo, self.thread_type, self.min_confidence]
        for widget in widgets:
            widget.blockSignals(True)

        self.set_search_text(query)
        self.set_shared_only(shared_only)
        self.set_parse_health(parse_health)
        self.set_sort_mode(sort_mode)
        self.set_thread_type(thread_type)
        self.set_min_confidence_pct(min_confidence_pct)

        for widget in widgets:
            widget.blockSignals(False)

        self.filters_changed.emit()

    def set_status(self, text: str) -> None:
        self.active_label.setText(text)
