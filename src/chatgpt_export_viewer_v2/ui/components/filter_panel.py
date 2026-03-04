from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QWidget,
)

from ...domain.enums import SortMode


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
        self.sort_combo.addItem("Title", SortMode.TITLE)

        self.shared_only = QCheckBox("Shared threads only", self)

        self.parse_health = QComboBox(self)
        self.parse_health.addItem("All", "all")
        self.parse_health.addItem("Healthy", "ok")
        self.parse_health.addItem("Partial", "partial")

        self.active_label = QLabel("Ready", self)
        self.active_label.setObjectName("mutedLabel")

        layout.addRow("Search", self.search_input)
        layout.addRow("Sort", self.sort_combo)
        layout.addRow("Scope", self.shared_only)
        layout.addRow("Health", self.parse_health)
        layout.addRow("Status", self.active_label)

        self.search_input.textChanged.connect(self.filters_changed.emit)
        self.sort_combo.currentIndexChanged.connect(self.filters_changed.emit)
        self.shared_only.toggled.connect(self.filters_changed.emit)
        self.parse_health.currentIndexChanged.connect(self.filters_changed.emit)

    def current_filters(self) -> dict:
        sort_mode = self.sort_combo.currentData()
        if sort_mode is None:
            sort_mode = SortMode.UPDATED
        return {
            "query": self.search_input.text(),
            "shared_only": self.shared_only.isChecked(),
            "parse_health": self.parse_health.currentData() or "all",
            "sort_mode": sort_mode,
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

    def restore_filters(self, query: str, shared_only: bool, parse_health: str, sort_mode: str) -> None:
        widgets = [self.search_input, self.shared_only, self.parse_health, self.sort_combo]
        for widget in widgets:
            widget.blockSignals(True)

        self.set_search_text(query)
        self.set_shared_only(shared_only)
        self.set_parse_health(parse_health)
        self.set_sort_mode(sort_mode)

        for widget in widgets:
            widget.blockSignals(False)

        self.filters_changed.emit()

    def set_status(self, text: str) -> None:
        self.active_label.setText(text)
