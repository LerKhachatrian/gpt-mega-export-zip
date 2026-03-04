from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from ...domain.models import HealthEvent


class HealthPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)

        self.list_widget = QListWidget(self)
        layout.addWidget(self.list_widget)

    def clear_events(self) -> None:
        self.list_widget.clear()

    def add_events(self, events: list[HealthEvent]) -> None:
        for event in events:
            line = f"[{event.level.upper()}] {event.code}: {event.message}"
            item = QListWidgetItem(line)
            if event.level.lower() == "warning":
                item.setForeground(Qt.GlobalColor.yellow)
            elif event.level.lower() == "error":
                item.setForeground(Qt.GlobalColor.red)
            else:
                item.setForeground(Qt.GlobalColor.lightGray)
            self.list_widget.addItem(item)
