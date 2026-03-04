from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QPushButton,
    QSpinBox,
    QWidget,
)

from ...config.defaults import MAX_JSON_FALLBACK_MB, PARSE_CHUNK_SIZE, THEME_DARK, THEME_LIGHT


class SettingsPage(QWidget):
    settings_changed = Signal(dict)
    cache_action_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = QFormLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        self.theme_combo = QComboBox(self)
        self.theme_combo.addItem("Dark", THEME_DARK)
        self.theme_combo.addItem("Light", THEME_LIGHT)

        self.parse_chunk = QSpinBox(self)
        self.parse_chunk.setRange(50, 5000)
        self.parse_chunk.setSingleStep(50)
        self.parse_chunk.setValue(PARSE_CHUNK_SIZE)

        self.json_fallback = QSpinBox(self)
        self.json_fallback.setRange(16, 1024)
        self.json_fallback.setSingleStep(16)
        self.json_fallback.setValue(MAX_JSON_FALLBACK_MB)

        self.rebuild_cache_btn = QPushButton("Rebuild current source cache", self)
        self.clear_current_cache_btn = QPushButton("Clear current source cache", self)
        self.clear_all_cache_btn = QPushButton("Clear all caches", self)

        cache_row = QWidget(self)
        cache_layout = QHBoxLayout(cache_row)
        cache_layout.setContentsMargins(0, 0, 0, 0)
        cache_layout.addWidget(self.rebuild_cache_btn)
        cache_layout.addWidget(self.clear_current_cache_btn)
        cache_layout.addWidget(self.clear_all_cache_btn)

        layout.addRow("Theme", self.theme_combo)
        layout.addRow("Parse chunk size", self.parse_chunk)
        layout.addRow("JSON fallback max MB", self.json_fallback)
        layout.addRow("Cache actions", cache_row)

        self.theme_combo.currentIndexChanged.connect(self._emit_changes)
        self.parse_chunk.valueChanged.connect(self._emit_changes)
        self.json_fallback.valueChanged.connect(self._emit_changes)

        self.rebuild_cache_btn.clicked.connect(lambda: self.cache_action_requested.emit("rebuild_current"))
        self.clear_current_cache_btn.clicked.connect(lambda: self.cache_action_requested.emit("clear_current"))
        self.clear_all_cache_btn.clicked.connect(lambda: self.cache_action_requested.emit("clear_all"))

    def _emit_changes(self) -> None:
        self.settings_changed.emit(self.current_settings())

    def current_settings(self) -> dict:
        return {
            "theme": self.theme_combo.currentData(),
            "parse_chunk_size": self.parse_chunk.value(),
            "max_json_fallback_mb": self.json_fallback.value(),
        }

    def set_theme(self, theme: str) -> None:
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == theme:
                self.theme_combo.setCurrentIndex(i)
                break
