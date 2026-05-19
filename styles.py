"""Shared styles for the Todo List application - supports dark/light themes."""


ACCENT_PRESETS = {
    "purple": {
        "primary": "#7c3aed",
        "primary_hover": "#6d28d9",
        "checkbox": "#7c3aed",
    },
    "blue": {
        "primary": "#2563eb",
        "primary_hover": "#1d4ed8",
        "checkbox": "#2563eb",
    },
    "green": {
        "primary": "#16a34a",
        "primary_hover": "#15803d",
        "checkbox": "#16a34a",
    },
    "orange": {
        "primary": "#ea580c",
        "primary_hover": "#c2410c",
        "checkbox": "#ea580c",
    },
    "rose": {
        "primary": "#e11d48",
        "primary_hover": "#be123c",
        "checkbox": "#e11d48",
    },
}

DARK_COLORS = {
    "bg": "#1e1e2e",
    "surface": "#2a2a3d",
    "surface_hover": "#33334d",
    "primary": "#7c3aed",
    "primary_hover": "#6d28d9",
    "accent": "#f59e0b",
    "accent_hover": "#d97706",
    "danger": "#ef4444",
    "danger_hover": "#dc2626",
    "success": "#10b981",
    "text": "#e2e8f0",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "border": "#3b3b55",
    "overdue": "#fca5a5",
    "star_active": "#fbbf24",
    "star_inactive": "#64748b",
    "checkbox": "#7c3aed",
}

LIGHT_COLORS = {
    "bg": "#f8f9fc",
    "surface": "#ffffff",
    "surface_hover": "#f0f1f5",
    "primary": "#7c3aed",
    "primary_hover": "#6d28d9",
    "accent": "#f59e0b",
    "accent_hover": "#d97706",
    "danger": "#ef4444",
    "danger_hover": "#dc2626",
    "success": "#10b981",
    "text": "#1e293b",
    "text_secondary": "#475569",
    "text_muted": "#94a3b8",
    "border": "#e2e8f0",
    "overdue": "#dc2626",
    "star_active": "#f59e0b",
    "star_inactive": "#94a3b8",
    "checkbox": "#7c3aed",
}

# Current active color palette  (mutable dict, updated in-place)
_current_theme = "light"
_current_accent = "purple"
COLORS: dict[str, str] = dict(LIGHT_COLORS)


def _apply_accent(colors: dict[str, str], accent_name: str) -> dict[str, str]:
    accent = ACCENT_PRESETS.get(accent_name, ACCENT_PRESETS["purple"])
    merged = dict(colors)
    merged["primary"] = accent["primary"]
    merged["primary_hover"] = accent["primary_hover"]
    merged["checkbox"] = accent["checkbox"]
    return merged


def set_theme(theme: str):
    """Switch theme. 'dark' or 'light'."""
    global _current_theme
    _current_theme = theme
    src = LIGHT_COLORS if theme == "light" else DARK_COLORS
    themed = _apply_accent(src, _current_accent)
    COLORS.clear()
    COLORS.update(themed)


def get_theme() -> str:
    return _current_theme


def set_accent_color(accent_name: str):
    """Switch global accent color preset."""
    global _current_accent
    _current_accent = accent_name if accent_name in ACCENT_PRESETS else "purple"
    set_theme(_current_theme)


def get_accent_color() -> str:
    return _current_accent


def build_main_stylesheet() -> str:
    return f"""
    QMainWindow, QDialog {{
        background-color: {COLORS['bg']};
        color: {COLORS['text']};
    }}
    QWidget {{
        color: {COLORS['text']};
        font-family: 'Segoe UI', 'Microsoft JhengHei', sans-serif;
        font-size: 13px;
    }}
    QLabel {{
        color: {COLORS['text']};
        background: transparent;
    }}
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {COLORS['surface']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 13px;
        selection-background-color: {COLORS['primary']};
    }}
    QLineEdit:focus, QTextEdit:focus {{
        border: 1px solid {COLORS['primary']};
    }}
    QPushButton {{
        background-color: {COLORS['primary']};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 18px;
        font-size: 13px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {COLORS['primary_hover']};
    }}
    QPushButton:pressed {{
        background-color: {COLORS['primary_hover']};
    }}
    QPushButton#dangerBtn {{
        background-color: {COLORS['danger']};
    }}
    QPushButton#dangerBtn:hover {{
        background-color: {COLORS['danger_hover']};
    }}
    QPushButton#ghostBtn {{
        background-color: transparent;
        color: {COLORS['text_secondary']};
        border: 1px solid {COLORS['border']};
    }}
    QPushButton#ghostBtn:hover {{
        background-color: {COLORS['surface']};
        color: {COLORS['text']};
    }}
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollBar:vertical {{
        background: {COLORS['bg']};
        width: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS['border']};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {COLORS['text_muted']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        height: 0px;
    }}
    QCheckBox {{
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 20px;
        height: 20px;
        border-radius: 4px;
        border: 2px solid {COLORS['border']};
        background: transparent;
    }}
    QCheckBox::indicator:checked {{
        background-color: {COLORS['primary']};
        border-color: {COLORS['primary']};
    }}
    QSlider::groove:horizontal {{
        border: none;
        height: 6px;
        background: {COLORS['surface']};
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: {COLORS['primary']};
        width: 18px;
        height: 18px;
        margin: -6px 0;
        border-radius: 9px;
    }}
    QSlider::handle:horizontal:hover {{
        background: {COLORS['primary_hover']};
    }}
    QSlider::sub-page:horizontal {{
        background: {COLORS['primary']};
        border-radius: 3px;
    }}
    QTabWidget::pane {{
        border: none;
        background: {COLORS['bg']};
    }}
    QTabBar::tab {{
        background: {COLORS['surface']};
        color: {COLORS['text_secondary']};
        border: none;
        border-radius: 8px 8px 0 0;
        padding: 8px 20px;
        margin-right: 2px;
        font-weight: 600;
    }}
    QTabBar::tab:selected {{
        background: {COLORS['primary']};
        color: white;
    }}
    QTabBar::tab:hover:!selected {{
        background: {COLORS['surface_hover']};
        color: {COLORS['text']};
    }}
    QCalendarWidget {{
        background-color: {COLORS['bg']};
        color: {COLORS['text']};
    }}
    QCalendarWidget QAbstractItemView {{
        background-color: {COLORS['surface']};
        color: {COLORS['text']};
        selection-background-color: {COLORS['primary']};
        selection-color: white;
        border-radius: 4px;
    }}
    QCalendarWidget QWidget#qt_calendar_navigationbar {{
        background-color: {COLORS['surface']};
    }}
    QCalendarWidget QToolButton {{
        color: {COLORS['text']};
        background: transparent;
        border: none;
        border-radius: 4px;
        padding: 4px 8px;
    }}
    QCalendarWidget QToolButton:hover {{
        background-color: {COLORS['surface_hover']};
    }}
    QCalendarWidget QSpinBox {{
        color: {COLORS['text']};
        background: {COLORS['surface']};
        border: none;
    }}
    QComboBox {{
        background-color: {COLORS['surface']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 6px 12px;
        font-size: 13px;
        min-height: 28px;
    }}
    QComboBox:hover {{
        border-color: {COLORS['primary']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border: none;
    }}
    QComboBox QAbstractItemView {{
        background-color: {COLORS['surface']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
        selection-background-color: {COLORS['primary']};
        selection-color: white;
        padding: 4px;
    }}
    """


def build_task_card_style() -> str:
    return f"""
    QFrame#taskCard {{
        background-color: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
    }}
    QFrame#taskCard:hover {{
        border-color: {COLORS['primary']};
        background-color: {COLORS['surface_hover']};
    }}
    """


def build_mini_mode_style() -> str:
    return f"""
    QWidget {{
        background-color: {COLORS['bg']};
        color: {COLORS['text']};
        font-family: 'Segoe UI', 'Microsoft JhengHei', sans-serif;
        font-size: 11px;
    }}
    QLabel {{
        background: transparent;
    }}
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollBar:vertical {{
        background: {COLORS['bg']};
        width: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS['border']};
        border-radius: 2px;
        min-height: 20px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    """
