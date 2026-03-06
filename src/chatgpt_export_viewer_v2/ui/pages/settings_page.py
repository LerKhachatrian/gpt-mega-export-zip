from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ...config.defaults import (
    DEFAULT_CODING_THRESHOLD,
    MAX_JSON_FALLBACK_MB,
    PARSE_CHUNK_SIZE,
    THEME_DARK,
    THEME_LIGHT,
)
from ...services.number_format_service import NUMBER_FORMAT_COMPACT, NUMBER_FORMAT_FULL, normalize_number_format_mode


class SettingsPage(QWidget):
    settings_changed = Signal(dict)
    cache_action_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_host = QWidget(scroll)
        scroll_host.setObjectName("settingsScrollHost")
        scroll.setWidget(scroll_host)
        root.addWidget(scroll)

        layout = QVBoxLayout(scroll_host)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        header_panel = QWidget(scroll_host)
        header_panel.setObjectName("settingsHeaderPanel")
        header_layout = QVBoxLayout(header_panel)
        header_layout.setContentsMargins(16, 14, 16, 14)
        header_layout.setSpacing(6)

        header_title = QLabel("Settings", header_panel)
        header_title.setObjectName("settingsTitle")
        header_subtitle = QLabel(
            "Tune parsing, analysis, formatting, and cache behavior for large exports.",
            header_panel,
        )
        header_subtitle.setObjectName("settingsSubtitle")
        header_subtitle.setWordWrap(True)

        header_layout.addWidget(header_title)
        header_layout.addWidget(header_subtitle)
        layout.addWidget(header_panel)

        self.theme_combo = QComboBox(self)
        self.theme_combo.addItem("Dark", THEME_DARK)
        self.theme_combo.addItem("Light", THEME_LIGHT)

        self.parse_chunk = QSpinBox(self)
        self.parse_chunk.setRange(50, 5000)
        self.parse_chunk.setSingleStep(50)
        self.parse_chunk.setValue(PARSE_CHUNK_SIZE)
        self.parse_chunk.setSuffix(" rows")

        self.json_fallback = QSpinBox(self)
        self.json_fallback.setRange(16, 1024)
        self.json_fallback.setSingleStep(16)
        self.json_fallback.setValue(MAX_JSON_FALLBACK_MB)
        self.json_fallback.setSuffix(" MB")

        self.coding_threshold_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.coding_threshold_slider.setRange(0, 100)
        self.coding_threshold_slider.setSingleStep(1)
        self.coding_threshold_slider.setValue(int(DEFAULT_CODING_THRESHOLD * 100))

        self.coding_threshold_spin = QSpinBox(self)
        self.coding_threshold_spin.setRange(0, 100)
        self.coding_threshold_spin.setSingleStep(1)
        self.coding_threshold_spin.setSuffix("%")
        self.coding_threshold_spin.setValue(int(DEFAULT_CODING_THRESHOLD * 100))

        threshold_row = QWidget(self)
        threshold_layout = QHBoxLayout(threshold_row)
        threshold_layout.setContentsMargins(0, 0, 0, 0)
        threshold_layout.setSpacing(8)
        threshold_layout.addWidget(self.coding_threshold_slider, 1)
        threshold_layout.addWidget(self.coding_threshold_spin)

        self.number_format_combo = QComboBox(self)
        self.number_format_combo.addItem("Compact (24.1M / 27.2K)", NUMBER_FORMAT_COMPACT)
        self.number_format_combo.addItem("Full (24,100,000 / 27,200)", NUMBER_FORMAT_FULL)

        self.rebuild_cache_btn = QPushButton("Rebuild current source cache", self)
        self.clear_current_cache_btn = QPushButton("Clear current source cache", self)
        self.clear_all_cache_btn = QPushButton("Clear all caches", self)
        self.rebuild_cache_btn.setObjectName("settingsActionNeutral")
        self.clear_current_cache_btn.setObjectName("settingsActionWarning")
        self.clear_all_cache_btn.setObjectName("settingsActionDanger")

        cache_row = QWidget(self)
        cache_layout = QHBoxLayout(cache_row)
        cache_layout.setContentsMargins(0, 0, 0, 0)
        cache_layout.setSpacing(8)
        cache_layout.addWidget(self.rebuild_cache_btn)
        cache_layout.addWidget(self.clear_current_cache_btn)
        cache_layout.addWidget(self.clear_all_cache_btn)

        appearance_section = self._build_section(
            parent=scroll_host,
            title="Appearance & Display",
            subtitle="Control visual theme and large-number formatting.",
        )
        appearance_layout = appearance_section.layout()
        appearance_layout.addWidget(
            self._build_setting_row(
                label="Theme",
                control=self.theme_combo,
                hint="Applied instantly to all views.",
            )
        )
        appearance_layout.addWidget(
            self._build_setting_row(
                label="Number format",
                control=self.number_format_combo,
                hint="Compact uses values like 24.1M and 27.2K.",
            )
        )
        layout.addWidget(appearance_section)

        performance_section = self._build_section(
            parent=scroll_host,
            title="Load Performance",
            subtitle="Tune parsing throughput and large-JSON memory behavior.",
        )
        performance_layout = performance_section.layout()
        performance_layout.addWidget(
            self._build_setting_row(
                label="Parse chunk size",
                control=self.parse_chunk,
                hint="Higher values can load faster but may increase UI pressure on slower systems.",
            )
        )
        performance_layout.addWidget(
            self._build_setting_row(
                label="JSON fallback limit",
                control=self.json_fallback,
                hint="Maximum size allowed for detailed JSON fallback reads.",
            )
        )
        layout.addWidget(performance_section)

        analysis_section = self._build_section(
            parent=scroll_host,
            title="Coding Analysis",
            subtitle="Define when a thread should be classified as primarily coding.",
        )
        analysis_layout = analysis_section.layout()
        analysis_layout.addWidget(
            self._build_setting_row(
                label="Coding threshold",
                control=threshold_row,
                hint="Threads at or above this code ratio are marked primarily coding.",
            )
        )
        layout.addWidget(analysis_section)

        cache_section = self._build_section(
            parent=scroll_host,
            title="Cache Management",
            subtitle="Rebuild or clear cache data without restarting the app.",
        )
        cache_section_layout = cache_section.layout()
        cache_section_layout.addWidget(
            self._build_setting_row(
                label="Cache actions",
                control=cache_row,
                hint="Use rebuild after changing source content or parser thresholds.",
            )
        )
        layout.addWidget(cache_section)

        footer_note = QLabel("Changes are saved automatically and applied live.", scroll_host)
        footer_note.setObjectName("settingsFooterNote")
        layout.addWidget(footer_note)
        layout.addStretch(1)

        self.theme_combo.currentIndexChanged.connect(self._emit_changes)
        self.parse_chunk.valueChanged.connect(self._emit_changes)
        self.json_fallback.valueChanged.connect(self._emit_changes)
        self.coding_threshold_slider.valueChanged.connect(self._on_threshold_slider_changed)
        self.coding_threshold_spin.valueChanged.connect(self._on_threshold_spin_changed)
        self.number_format_combo.currentIndexChanged.connect(self._emit_changes)

        self.rebuild_cache_btn.clicked.connect(lambda: self.cache_action_requested.emit("rebuild_current"))
        self.clear_current_cache_btn.clicked.connect(lambda: self.cache_action_requested.emit("clear_current"))
        self.clear_all_cache_btn.clicked.connect(lambda: self.cache_action_requested.emit("clear_all"))

    def _build_section(self, parent: QWidget, title: str, subtitle: str) -> QWidget:
        section = QWidget(parent)
        section.setObjectName("settingsSection")

        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(14, 14, 14, 14)
        section_layout.setSpacing(10)

        title_label = QLabel(title, section)
        title_label.setObjectName("settingsSectionTitle")

        subtitle_label = QLabel(subtitle, section)
        subtitle_label.setObjectName("settingsSectionSubtitle")
        subtitle_label.setWordWrap(True)

        section_layout.addWidget(title_label)
        section_layout.addWidget(subtitle_label)
        return section

    def _build_setting_row(self, label: str, control: QWidget, hint: str = "") -> QWidget:
        row = QWidget(self)
        row.setObjectName("settingsRow")

        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(10, 8, 10, 8)
        row_layout.setSpacing(6)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(10)

        label_widget = QLabel(label, row)
        label_widget.setObjectName("settingsRowLabel")
        label_widget.setMinimumWidth(170)

        top.addWidget(label_widget)
        top.addWidget(control, 1)

        row_layout.addLayout(top)

        if hint:
            hint_label = QLabel(hint, row)
            hint_label.setObjectName("settingsRowHint")
            hint_label.setWordWrap(True)
            row_layout.addWidget(hint_label)

        return row

    def _on_threshold_slider_changed(self, value: int) -> None:
        if self.coding_threshold_spin.value() != value:
            self.coding_threshold_spin.blockSignals(True)
            self.coding_threshold_spin.setValue(value)
            self.coding_threshold_spin.blockSignals(False)
        self._emit_changes()

    def _on_threshold_spin_changed(self, value: int) -> None:
        if self.coding_threshold_slider.value() != value:
            self.coding_threshold_slider.blockSignals(True)
            self.coding_threshold_slider.setValue(value)
            self.coding_threshold_slider.blockSignals(False)
        self._emit_changes()

    def _emit_changes(self) -> None:
        self.settings_changed.emit(self.current_settings())

    def current_settings(self) -> dict:
        return {
            "theme": self.theme_combo.currentData(),
            "parse_chunk_size": self.parse_chunk.value(),
            "max_json_fallback_mb": self.json_fallback.value(),
            "coding_threshold_pct": self.coding_threshold_spin.value(),
            "number_format_mode": normalize_number_format_mode(str(self.number_format_combo.currentData() or "")),
        }

    def set_theme(self, theme: str) -> None:
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == theme:
                self.theme_combo.blockSignals(True)
                self.theme_combo.setCurrentIndex(i)
                self.theme_combo.blockSignals(False)
                break

    def set_parse_chunk_size(self, value: int) -> None:
        self.parse_chunk.blockSignals(True)
        self.parse_chunk.setValue(max(self.parse_chunk.minimum(), min(self.parse_chunk.maximum(), int(value))))
        self.parse_chunk.blockSignals(False)

    def set_max_json_fallback_mb(self, value: int) -> None:
        self.json_fallback.blockSignals(True)
        self.json_fallback.setValue(max(self.json_fallback.minimum(), min(self.json_fallback.maximum(), int(value))))
        self.json_fallback.blockSignals(False)

    def set_coding_threshold_pct(self, value: int) -> None:
        clamped = max(0, min(100, int(value)))
        self.coding_threshold_slider.blockSignals(True)
        self.coding_threshold_spin.blockSignals(True)
        self.coding_threshold_slider.setValue(clamped)
        self.coding_threshold_spin.setValue(clamped)
        self.coding_threshold_slider.blockSignals(False)
        self.coding_threshold_spin.blockSignals(False)

    def set_number_format_mode(self, mode: str) -> None:
        target = normalize_number_format_mode(mode)
        for index in range(self.number_format_combo.count()):
            data = str(self.number_format_combo.itemData(index) or "")
            if data == target:
                self.number_format_combo.blockSignals(True)
                self.number_format_combo.setCurrentIndex(index)
                self.number_format_combo.blockSignals(False)
                return
