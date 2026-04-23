"""Settings panel with transparency, always-on-top, auto-startup, language and theme."""

import sys
import os
import winreg

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QCheckBox, QPushButton,
    QComboBox, QFrame, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from styles import COLORS, get_theme, get_accent_color
from i18n import t, get_language


APP_NAME = "TodoListApp"


def get_startup_registry_value():
    """Get the current auto-startup registry entry, if any."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_READ
        )
        value, _ = winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return value
    except (FileNotFoundError, OSError):
        return None


def set_auto_startup(enable: bool):
    """Add or remove the application from Windows startup."""
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0, winreg.KEY_SET_VALUE
    )
    if enable:
        exe_path = sys.executable
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}" "{script_path}"')
    else:
        try:
            winreg.DeleteValue(key, APP_NAME)
        except FileNotFoundError:
            pass
    winreg.CloseKey(key)


class SettingsPanel(QWidget):
    """Settings panel widget."""

    opacity_changed = pyqtSignal(float)
    always_on_top_changed = pyqtSignal(bool)
    mini_mode_requested = pyqtSignal()
    mini_size_changed = pyqtSignal(int, int)
    language_changed = pyqtSignal(str)
    theme_changed = pyqtSignal(str)
    accent_changed = pyqtSignal(str)
    kanban_min_width_changed = pyqtSignal(int)
    mini_views_changed = pyqtSignal(list)
    mini_gadgets_changed = pyqtSignal(bool, bool, bool)
    mini_clock_theme_changed = pyqtSignal(str)

    MINI_DEFAULT_W = 200
    MINI_DEFAULT_H = 380
    KANBAN_MIN_COL_DEFAULT = 260

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(24)

        # Section: Settings Title
        self.section_label = QLabel(t("settings_title"))
        self.section_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        layout.addWidget(self.section_label)

        # --- Language ---
        lang_layout = QHBoxLayout()
        lang_layout.setSpacing(12)
        self.lang_label = QLabel(t("language_label"))
        self.lang_label.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        lang_layout.addWidget(self.lang_label)
        lang_layout.addStretch()

        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("繁體中文", "zh_tw")
        current_lang = get_language()
        idx = 0 if current_lang == "en" else 1
        self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.setMinimumWidth(140)
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)

        self._add_separator(layout)

        # --- Kanban Options ---
        self.kanban_title_label = QLabel(t("kanban_settings_title"))
        self.kanban_title_label.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        layout.addWidget(self.kanban_title_label)

        kanban_width_row = QHBoxLayout()
        kanban_width_row.setSpacing(10)

        self.kanban_min_width_label = QLabel(t("kanban_min_width"))
        self.kanban_min_width_label.setFont(QFont("Segoe UI", 12))
        kanban_width_row.addWidget(self.kanban_min_width_label)

        self.kanban_min_width_spin = QSpinBox()
        self.kanban_min_width_spin.setMinimum(180)
        self.kanban_min_width_spin.setMaximum(420)
        self.kanban_min_width_spin.setValue(self.KANBAN_MIN_COL_DEFAULT)
        self.kanban_min_width_spin.setSuffix(" px")
        self.kanban_min_width_spin.setMinimumHeight(32)
        self.kanban_min_width_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS['surface']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
            }}
            QSpinBox:focus {{ border-color: {COLORS['primary']}; }}
        """)
        self.kanban_min_width_spin.valueChanged.connect(
            lambda value: self.kanban_min_width_changed.emit(int(value))
        )
        kanban_width_row.addWidget(self.kanban_min_width_spin)

        self.kanban_width_reset_btn = QPushButton(t("reset_default"))
        self.kanban_width_reset_btn.setObjectName("ghostBtn")
        self.kanban_width_reset_btn.setFont(QFont("Segoe UI", 11))
        self.kanban_width_reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.kanban_width_reset_btn.clicked.connect(self._reset_kanban_width)
        kanban_width_row.addWidget(self.kanban_width_reset_btn)

        kanban_width_row.addStretch()

        layout.addLayout(kanban_width_row)

        self._add_separator(layout)

        # --- Theme ---
        theme_layout = QHBoxLayout()
        theme_layout.setSpacing(12)
        self.theme_label = QLabel(t("theme_label"))
        self.theme_label.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        theme_layout.addWidget(self.theme_label)
        theme_layout.addStretch()

        self.theme_combo = QComboBox()
        self.theme_combo.addItem(t("theme_dark"), "dark")
        self.theme_combo.addItem(t("theme_light"), "light")
        current_theme = get_theme()
        self.theme_combo.setCurrentIndex(0 if current_theme == "dark" else 1)
        self.theme_combo.setMinimumWidth(140)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)

        color_layout = QHBoxLayout()
        color_layout.setSpacing(12)
        self.color_label = QLabel(t("color_label"))
        self.color_label.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        color_layout.addWidget(self.color_label)
        color_layout.addStretch()

        self.color_combo = QComboBox()
        self.color_combo.addItem(t("color_purple"), "purple")
        self.color_combo.addItem(t("color_blue"), "blue")
        self.color_combo.addItem(t("color_green"), "green")
        self.color_combo.addItem(t("color_orange"), "orange")
        self.color_combo.addItem(t("color_rose"), "rose")
        self.color_combo.setMinimumWidth(140)
        self.color_combo.currentIndexChanged.connect(self._on_accent_changed)
        color_layout.addWidget(self.color_combo)
        layout.addLayout(color_layout)

        clock_theme_layout = QHBoxLayout()
        clock_theme_layout.setSpacing(12)
        self.clock_theme_label = QLabel(t("clock_theme"))
        self.clock_theme_label.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        clock_theme_layout.addWidget(self.clock_theme_label)
        clock_theme_layout.addStretch()

        self.clock_theme_combo = QComboBox()
        self.clock_theme_combo.addItem(t("clock_theme_classic"), "classic")
        self.clock_theme_combo.addItem(t("clock_theme_neon"), "neon")
        self.clock_theme_combo.addItem(t("clock_theme_minimal"), "minimal")
        self.clock_theme_combo.setMinimumWidth(140)
        self.clock_theme_combo.currentIndexChanged.connect(self._on_clock_theme_changed)
        clock_theme_layout.addWidget(self.clock_theme_combo)
        layout.addLayout(clock_theme_layout)

        self.set_accent(get_accent_color())

        self._add_separator(layout)

        # --- Transparency ---
        trans_layout = QVBoxLayout()
        trans_layout.setSpacing(8)

        trans_header = QHBoxLayout()
        self.trans_label = QLabel(t("window_opacity"))
        self.trans_label.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        trans_header.addWidget(self.trans_label)

        self.opacity_value_label = QLabel("100%")
        self.opacity_value_label.setFont(QFont("Segoe UI", 13))
        self.opacity_value_label.setStyleSheet(f"color: {COLORS['primary']};")
        self.opacity_value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        trans_header.addWidget(self.opacity_value_label)

        trans_layout.addLayout(trans_header)

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setMinimum(10)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setTickInterval(10)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        trans_layout.addWidget(self.opacity_slider)

        layout.addLayout(trans_layout)

        self._add_separator(layout)

        # --- Always on Top ---
        self.on_top_check = QCheckBox(t("always_on_top"))
        self.on_top_check.setFont(QFont("Segoe UI", 13))
        self.on_top_check.stateChanged.connect(
            lambda state: self.always_on_top_changed.emit(bool(state))
        )
        layout.addWidget(self.on_top_check)

        self._add_separator(layout)

        # --- Auto Startup ---
        self.startup_check = QCheckBox(t("auto_startup"))
        self.startup_check.setFont(QFont("Segoe UI", 13))
        self.startup_check.setChecked(get_startup_registry_value() is not None)
        self.startup_check.stateChanged.connect(
            lambda state: set_auto_startup(bool(state))
        )
        layout.addWidget(self.startup_check)

        self._add_separator(layout)

        # --- Mini Window Size ---
        mini_size_header = QHBoxLayout()
        self.mini_size_label = QLabel(t("mini_size"))
        self.mini_size_label.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        mini_size_header.addWidget(self.mini_size_label)
        mini_size_header.addStretch()

        self.mini_reset_btn = QPushButton(t("reset_default"))
        self.mini_reset_btn.setObjectName("ghostBtn")
        self.mini_reset_btn.setFont(QFont("Segoe UI", 11))
        self.mini_reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mini_reset_btn.clicked.connect(self._reset_mini_size)
        mini_size_header.addWidget(self.mini_reset_btn)

        layout.addLayout(mini_size_header)

        size_row = QHBoxLayout()
        size_row.setSpacing(12)

        self.width_label = QLabel(t("width"))
        self.width_label.setFont(QFont("Segoe UI", 12))
        size_row.addWidget(self.width_label)

        self.mini_width_spin = QSpinBox()
        self.mini_width_spin.setMinimum(150)
        self.mini_width_spin.setMaximum(500)
        self.mini_width_spin.setValue(self.MINI_DEFAULT_W)
        self.mini_width_spin.setSuffix(" px")
        self.mini_width_spin.setMinimumHeight(32)
        self.mini_width_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS['surface']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
            }}
            QSpinBox:focus {{ border-color: {COLORS['primary']}; }}
        """)
        self.mini_width_spin.valueChanged.connect(self._on_mini_size_changed)
        size_row.addWidget(self.mini_width_spin)

        size_row.addSpacing(8)

        self.height_label = QLabel(t("height"))
        self.height_label.setFont(QFont("Segoe UI", 12))
        size_row.addWidget(self.height_label)

        self.mini_height_spin = QSpinBox()
        self.mini_height_spin.setMinimum(200)
        self.mini_height_spin.setMaximum(800)
        self.mini_height_spin.setValue(self.MINI_DEFAULT_H)
        self.mini_height_spin.setSuffix(" px")
        self.mini_height_spin.setMinimumHeight(32)
        self.mini_height_spin.setStyleSheet(self.mini_width_spin.styleSheet())
        self.mini_height_spin.valueChanged.connect(self._on_mini_size_changed)
        size_row.addWidget(self.mini_height_spin)

        layout.addLayout(size_row)

        self._add_separator(layout)

        # --- Mini Window Content ---
        self.mini_views_label = QLabel(t("mini_views_title"))
        self.mini_views_label.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        layout.addWidget(self.mini_views_label)

        mini_views_row = QHBoxLayout()
        mini_views_row.setSpacing(12)

        self.mini_view_tasks_check = QCheckBox(t("mini_view_tasks"))
        self.mini_view_quick_check = QCheckBox(t("mini_view_quick"))
        self.mini_view_kanban_check = QCheckBox(t("mini_view_kanban"))
        self.mini_view_clock_check = QCheckBox(t("mini_view_clock"))
        for check in (self.mini_view_tasks_check, self.mini_view_quick_check, self.mini_view_kanban_check, self.mini_view_clock_check):
            check.setFont(QFont("Segoe UI", 13))
            check.stateChanged.connect(self._on_mini_views_changed)
            mini_views_row.addWidget(check)

        mini_views_row.addStretch()
        layout.addLayout(mini_views_row)

        self._mini_view_checks = {
            "tasks": self.mini_view_tasks_check,
            "quick": self.mini_view_quick_check,
            "kanban": self.mini_view_kanban_check,
            "clock": self.mini_view_clock_check,
        }

        self._add_separator(layout)

        # --- Mini Gadgets ---
        self.mini_gadgets_label = QLabel(t("mini_gadgets_title"))
        self.mini_gadgets_label.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        layout.addWidget(self.mini_gadgets_label)

        mini_gadgets_row = QHBoxLayout()
        mini_gadgets_row.setSpacing(12)

        self.mini_gadgets_enable_check = QCheckBox(t("mini_gadgets_enable"))
        self.mini_gadget_clock_check = QCheckBox(t("mini_gadget_clock"))
        self.mini_gadget_digital_check = QCheckBox(t("mini_gadget_digital"))
        for check in (self.mini_gadgets_enable_check, self.mini_gadget_clock_check, self.mini_gadget_digital_check):
            check.setFont(QFont("Segoe UI", 13))
            check.stateChanged.connect(self._on_mini_gadgets_changed)
            mini_gadgets_row.addWidget(check)

        mini_gadgets_row.addStretch()
        layout.addLayout(mini_gadgets_row)

        # --- Mini Mode ---
        self.mini_btn = QPushButton(t("mini_mode_btn"))
        self.mini_btn.setMinimumHeight(44)
        self.mini_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        self.mini_btn.clicked.connect(self.mini_mode_requested.emit)
        layout.addWidget(self.mini_btn)

        layout.addStretch()

    def _add_separator(self, layout):
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']};")
        layout.addWidget(sep)

    def _on_opacity_changed(self, value):
        opacity = value / 100.0
        self.opacity_value_label.setText(f"{value}%")
        self.opacity_changed.emit(opacity)

    def _on_language_changed(self, index):
        lang = self.lang_combo.itemData(index)
        if lang:
            self.language_changed.emit(lang)

    def _on_theme_changed(self, index):
        theme = self.theme_combo.itemData(index)
        if theme:
            self.theme_changed.emit(theme)

    def _on_accent_changed(self, index):
        accent = self.color_combo.itemData(index)
        if accent:
            self.accent_changed.emit(accent)

    def _on_clock_theme_changed(self, index):
        theme = self.clock_theme_combo.itemData(index)
        if theme:
            self.mini_clock_theme_changed.emit(theme)

    def retranslate(self):
        """Update all labels after language change."""
        self.section_label.setText(t("settings_title"))
        self.lang_label.setText(t("language_label"))
        self.theme_label.setText(t("theme_label"))
        self.color_label.setText(t("color_label"))
        self.clock_theme_label.setText(t("clock_theme"))
        self.trans_label.setText(t("window_opacity"))
        self.on_top_check.setText(t("always_on_top"))
        self.startup_check.setText(t("auto_startup"))
        self.mini_btn.setText(t("mini_mode_btn"))
        self.mini_size_label.setText(t("mini_size"))
        self.mini_reset_btn.setText(t("reset_default"))
        self.width_label.setText(t("width"))
        self.height_label.setText(t("height"))
        self.kanban_title_label.setText(t("kanban_settings_title"))
        self.kanban_min_width_label.setText(t("kanban_min_width"))
        self.kanban_width_reset_btn.setText(t("reset_default"))
        self.mini_views_label.setText(t("mini_views_title"))
        self.mini_view_tasks_check.setText(t("mini_view_tasks"))
        self.mini_view_quick_check.setText(t("mini_view_quick"))
        self.mini_view_kanban_check.setText(t("mini_view_kanban"))
        self.mini_view_clock_check.setText(t("mini_view_clock"))
        self.mini_gadgets_label.setText(t("mini_gadgets_title"))
        self.mini_gadgets_enable_check.setText(t("mini_gadgets_enable"))
        self.mini_gadget_clock_check.setText(t("mini_gadget_clock"))
        self.mini_gadget_digital_check.setText(t("mini_gadget_digital"))
        # Update theme combo text
        self.theme_combo.blockSignals(True)
        cur_idx = self.theme_combo.currentIndex()
        self.theme_combo.setItemText(0, t("theme_dark"))
        self.theme_combo.setItemText(1, t("theme_light"))
        self.theme_combo.setCurrentIndex(cur_idx)
        self.theme_combo.blockSignals(False)

        self.color_combo.blockSignals(True)
        color_idx = self.color_combo.currentIndex()
        self.color_combo.setItemText(0, t("color_purple"))
        self.color_combo.setItemText(1, t("color_blue"))
        self.color_combo.setItemText(2, t("color_green"))
        self.color_combo.setItemText(3, t("color_orange"))
        self.color_combo.setItemText(4, t("color_rose"))
        self.color_combo.setCurrentIndex(color_idx)
        self.color_combo.blockSignals(False)

        self.clock_theme_combo.blockSignals(True)
        clock_idx = self.clock_theme_combo.currentIndex()
        self.clock_theme_combo.setItemText(0, t("clock_theme_classic"))
        self.clock_theme_combo.setItemText(1, t("clock_theme_neon"))
        self.clock_theme_combo.setItemText(2, t("clock_theme_minimal"))
        self.clock_theme_combo.setCurrentIndex(clock_idx)
        self.clock_theme_combo.blockSignals(False)

    def _on_mini_size_changed(self):
        w = self.mini_width_spin.value()
        h = self.mini_height_spin.value()
        self.mini_size_changed.emit(w, h)

    def _reset_mini_size(self):
        self.mini_width_spin.setValue(self.MINI_DEFAULT_W)
        self.mini_height_spin.setValue(self.MINI_DEFAULT_H)

    def set_kanban_layout(self, min_width: int):
        self.kanban_min_width_spin.blockSignals(True)
        self.kanban_min_width_spin.setValue(max(180, min(420, int(min_width))))
        self.kanban_min_width_spin.blockSignals(False)

    def _reset_kanban_width(self):
        self.kanban_min_width_spin.setValue(self.KANBAN_MIN_COL_DEFAULT)

    def _on_mini_views_changed(self, *args):
        enabled = self.get_mini_visible_views()
        if not enabled:
            self.mini_view_tasks_check.blockSignals(True)
            self.mini_view_tasks_check.setChecked(True)
            self.mini_view_tasks_check.blockSignals(False)
            enabled = ["tasks"]
        self.mini_views_changed.emit(enabled)

    def get_mini_visible_views(self) -> list[str]:
        views = []
        if self.mini_view_tasks_check.isChecked():
            views.append("tasks")
        if self.mini_view_quick_check.isChecked():
            views.append("quick")
        if self.mini_view_kanban_check.isChecked():
            views.append("kanban")
        if self.mini_view_clock_check.isChecked():
            views.append("clock")
        return views

    def set_mini_visible_views(self, views: list[str]):
        normalized = set(views or [])
        if not normalized:
            normalized = {"tasks"}
        for key, check in self._mini_view_checks.items():
            check.blockSignals(True)
            check.setChecked(key in normalized)
            check.blockSignals(False)

    def _on_mini_gadgets_changed(self, *args):
        enabled = self.mini_gadgets_enable_check.isChecked()
        show_clock = self.mini_gadget_clock_check.isChecked()
        show_digital = self.mini_gadget_digital_check.isChecked()
        if enabled and not (show_clock or show_digital):
            self.mini_gadget_clock_check.blockSignals(True)
            self.mini_gadget_clock_check.setChecked(True)
            self.mini_gadget_clock_check.blockSignals(False)
            show_clock = True
        self.mini_gadgets_changed.emit(enabled, show_clock, show_digital)

    def set_mini_gadgets(self, enabled: bool, show_clock: bool, show_digital: bool):
        self.mini_gadgets_enable_check.blockSignals(True)
        self.mini_gadget_clock_check.blockSignals(True)
        self.mini_gadget_digital_check.blockSignals(True)
        self.mini_gadgets_enable_check.setChecked(bool(enabled))
        self.mini_gadget_clock_check.setChecked(bool(show_clock))
        self.mini_gadget_digital_check.setChecked(bool(show_digital))
        self.mini_gadgets_enable_check.blockSignals(False)
        self.mini_gadget_clock_check.blockSignals(False)
        self.mini_gadget_digital_check.blockSignals(False)

    def set_clock_theme(self, clock_theme: str):
        idx = self.clock_theme_combo.findData(clock_theme)
        if idx < 0:
            idx = 0
        self.clock_theme_combo.blockSignals(True)
        self.clock_theme_combo.setCurrentIndex(idx)
        self.clock_theme_combo.blockSignals(False)

    def set_accent(self, accent: str):
        idx = self.color_combo.findData(accent)
        if idx < 0:
            idx = 0
        self.color_combo.blockSignals(True)
        self.color_combo.setCurrentIndex(idx)
        self.color_combo.blockSignals(False)
