"""Mini-mode window for the Todo List application."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QSlider, QCheckBox, QToolButton, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor, QAction

from styles import COLORS, build_mini_mode_style
from database import get_active_tasks, get_board_categories, get_quick_tasks
from date_utils import format_due_date, is_overdue
from i18n import t


class MiniMode(QWidget):
    """Compact mini-mode window showing urgent tasks."""

    restore_requested = pyqtSignal()
    view_mode_changed = pyqtSignal(str)

    def __init__(self, opacity=1.0, on_top=True, width=200, height=380, view_mode="tasks", visible_views=None, parent=None):
        super().__init__(parent)
        self._on_top = on_top
        self._opacity = opacity
        self._w = width
        self._h = height
        self._visible_views = self._normalize_visible_views(visible_views)
        self._view_mode = view_mode if view_mode in self._visible_views else (self._visible_views[0] if self._visible_views else "tasks")
        self.setWindowTitle("Todo")
        self.setFixedSize(self._w, self._h)
        self._apply_window_flags()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet(build_mini_mode_style())
        self.setWindowOpacity(self._opacity)
        self._drag_pos = None
        self._build_ui()
        self.refresh()

    def _normalize_visible_views(self, views):
        normalized = []
        for view in views or ["tasks", "kanban"]:
            if view in ("tasks", "quick", "kanban") and view not in normalized:
                normalized.append(view)
        return normalized or ["tasks"]

    def _apply_window_flags(self):
        flags = Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint
        if self._on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Title bar
        title_bar = QHBoxLayout()
        title_bar.setSpacing(4)

        self.title_label = QLabel(t("mini_title"))
        self.title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title_bar.addWidget(self.title_label, 1)

        self.cycle_btn = QPushButton("🔄")
        self.cycle_btn.setFixedSize(24, 24)
        self.cycle_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.cycle_btn.setObjectName("ghostBtn")
        self.cycle_btn.setToolTip(t("mini_cycle_view"))
        self.cycle_btn.clicked.connect(self._toggle_view_mode)
        title_bar.addWidget(self.cycle_btn)

        self.view_menu_btn = QToolButton()
        self.view_menu_btn.setText("☰")
        self.view_menu_btn.setFixedSize(24, 24)
        self.view_menu_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.view_menu_btn.setObjectName("ghostBtn")
        self.view_menu_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.view_menu = QMenu(self)
        self.view_menu_btn.setMenu(self.view_menu)
        self._rebuild_view_menu()
        title_bar.addWidget(self.view_menu_btn)

        restore_btn = QPushButton("⬜")
        restore_btn.setFixedSize(24, 24)
        restore_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        restore_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['text_secondary']};
                border: none;
                font-size: 12px;
            }}
            QPushButton:hover {{
                color: {COLORS['text']};
                background: {COLORS['surface']};
                border-radius: 4px;
            }}
        """)
        restore_btn.setToolTip(t("restore_tooltip"))
        restore_btn.clicked.connect(self.restore_requested.emit)
        title_bar.addWidget(restore_btn)

        self._update_mode_button_text()

        layout.addLayout(title_bar)

        # Controls row: opacity slider + on-top toggle
        controls = QHBoxLayout()
        controls.setSpacing(4)

        # Opacity slider (compact)
        self.mini_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.mini_opacity_slider.setMinimum(10)
        self.mini_opacity_slider.setMaximum(100)
        self.mini_opacity_slider.setValue(int(self._opacity * 100))
        self.mini_opacity_slider.setFixedWidth(80)
        self.mini_opacity_slider.setFixedHeight(16)
        self.mini_opacity_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: none; height: 4px;
                background: {COLORS['surface']}; border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['primary']}; width: 12px; height: 12px;
                margin: -4px 0; border-radius: 6px;
            }}
            QSlider::sub-page:horizontal {{
                background: {COLORS['primary']}; border-radius: 2px;
            }}
        """)
        self.mini_opacity_slider.valueChanged.connect(self._on_opacity_changed)
        controls.addWidget(self.mini_opacity_slider)

        self.mini_opacity_label = QLabel(f"{int(self._opacity*100)}%")
        self.mini_opacity_label.setFont(QFont("Segoe UI", 8))
        self.mini_opacity_label.setFixedWidth(28)
        controls.addWidget(self.mini_opacity_label)

        # On-top checkbox
        self.on_top_check = QCheckBox("📌")
        self.on_top_check.setChecked(self._on_top)
        self.on_top_check.setToolTip(t("always_on_top"))
        self.on_top_check.setStyleSheet("QCheckBox::indicator { width: 0; height: 0; } QCheckBox { font-size: 13px; }")
        self.on_top_check.stateChanged.connect(self._on_top_changed)
        controls.addWidget(self.on_top_check)

        layout.addLayout(controls)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {COLORS['border']};")
        layout.addWidget(sep)

        # Scrollable task list
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 4, 0, 4)
        self.container_layout.setSpacing(4)
        self.container_layout.addStretch()

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

    def refresh(self):
        """Reload active tasks into the mini view."""
        while self.container_layout.count() > 1:
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tasks = self._get_tasks_for_view()

        if not tasks:
            empty = QLabel(self._empty_text_for_view())
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setFont(QFont("Segoe UI", 10))
            empty.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 20px;")
            self.container_layout.insertWidget(0, empty)
            return

        if self._view_mode == "kanban":
            self._render_kanban_mode(tasks)
        elif self._view_mode == "quick":
            for task in tasks:
                card = self._create_mini_card(task)
                self.container_layout.insertWidget(self.container_layout.count() - 1, card)
        else:
            for task in tasks:
                card = self._create_mini_card(task)
                self.container_layout.insertWidget(self.container_layout.count() - 1, card)

    def _get_tasks_for_view(self):
        if self._view_mode == "quick":
            return get_quick_tasks()
        if self._view_mode == "kanban":
            return get_active_tasks(include_quick=False)
        return get_active_tasks(include_quick=False)

    def _empty_text_for_view(self):
        if self._view_mode == "quick":
            return t("quick_empty")
        return t("all_done")

    def _render_kanban_mode(self, tasks: list[dict]):
        grouped: dict[object, list[dict]] = {None: []}
        categories = get_board_categories()
        for cat in categories:
            grouped[cat["id"]] = []

        for task in tasks:
            cat_id = task.get("category_id")
            if cat_id not in grouped:
                cat_id = None
            grouped[cat_id].append(task)

        self._insert_mini_section(t("kanban_uncategorized"), grouped.get(None, []), "")
        for cat in categories:
            self._insert_mini_section(
                cat.get("name", ""),
                grouped.get(cat["id"], []),
                cat.get("color", ""),
            )

    def _insert_mini_section(self, title: str, tasks: list[dict], color: str):
        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-left: 4px solid {color or COLORS['border']};
                border-radius: 6px;
            }}
        """)
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(6, 6, 6, 6)
        section_layout.setSpacing(4)

        header = QLabel(f"{title} ({len(tasks)})")
        header.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        section_layout.addWidget(header)

        if not tasks:
            empty = QLabel("-")
            empty.setStyleSheet(f"color: {COLORS['text_muted']};")
            section_layout.addWidget(empty)
        else:
            for task in tasks:
                row = QLabel(f"• {task.get('title', '')}")
                row.setWordWrap(True)
                row.setFont(QFont("Segoe UI", 8))
                row.setStyleSheet(f"color: {COLORS['text_secondary']};")
                section_layout.addWidget(row)

        self.container_layout.insertWidget(self.container_layout.count() - 1, section)

    def _create_mini_card(self, task):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['surface']};
                border-radius: 6px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(8, 6, 8, 6)
        card_layout.setSpacing(2)

        # Title row
        title_row = QHBoxLayout()
        title_row.setSpacing(4)

        if task.get("is_starred"):
            star = QLabel("★")
            star.setStyleSheet(f"color: {COLORS['star_active']}; font-size: 10px;")
            star.setFixedWidth(14)
            title_row.addWidget(star)

        title = QLabel(task["title"])
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        title.setWordWrap(True)
        title_row.addWidget(title, 1)

        card_layout.addLayout(title_row)

        # Due date
        due = format_due_date(task.get("due_date"))
        if task.get("due_date"):
            due_label = QLabel(due)
            due_label.setFont(QFont("Segoe UI", 8))
            color = COLORS['overdue'] if is_overdue(task.get("due_date")) else COLORS['text_muted']
            due_label.setStyleSheet(f"color: {color};")
            card_layout.addWidget(due_label)

        return card

    def _on_opacity_changed(self, value):
        self._opacity = value / 100.0
        self.setWindowOpacity(self._opacity)
        self.mini_opacity_label.setText(f"{value}%")

    def _on_top_changed(self, state):
        self._on_top = bool(state)
        self._apply_window_flags()
        self.show()

    def _toggle_view_mode(self):
        if not self._visible_views:
            return
        if self._view_mode not in self._visible_views:
            self._view_mode = self._visible_views[0]
        else:
            idx = self._visible_views.index(self._view_mode)
            self._view_mode = self._visible_views[(idx + 1) % len(self._visible_views)]
        self._update_mode_button_text()
        self.view_mode_changed.emit(self._view_mode)
        self.refresh()

    def _update_mode_button_text(self):
        self.cycle_btn.setToolTip(t("mini_cycle_view"))
        self.view_menu_btn.setToolTip(t("mini_select_view"))
        self._rebuild_view_menu()

    def _rebuild_view_menu(self):
        self.view_menu.clear()
        labels = {
            "tasks": t("mini_view_tasks"),
            "quick": t("mini_view_quick"),
            "kanban": t("mini_view_kanban"),
        }
        for view in self._visible_views:
            action = QAction(labels.get(view, view), self)
            action.setCheckable(True)
            action.setChecked(view == self._view_mode)
            action.triggered.connect(lambda checked=False, v=view: self.set_view_mode(v))
            self.view_menu.addAction(action)

    def set_view_mode(self, mode: str):
        if mode not in self._visible_views:
            return
        self._view_mode = mode
        self._update_mode_button_text()
        self.view_mode_changed.emit(self._view_mode)
        self.refresh()

    def set_visible_views(self, views):
        self._visible_views = self._normalize_visible_views(views)
        if self._view_mode not in self._visible_views:
            self._view_mode = self._visible_views[0]
            self.view_mode_changed.emit(self._view_mode)
        self._update_mode_button_text()
        self.refresh()

    def retranslate(self):
        """Update labels after language changes."""
        self.setWindowTitle("Todo")
        self.title_label.setText(t("mini_title"))
        self._update_mode_button_text()

    def set_opacity(self, opacity):
        """Set opacity externally (from settings)."""
        self._opacity = opacity
        self.setWindowOpacity(opacity)
        self.mini_opacity_slider.blockSignals(True)
        self.mini_opacity_slider.setValue(int(opacity * 100))
        self.mini_opacity_slider.blockSignals(False)
        self.mini_opacity_label.setText(f"{int(opacity*100)}%")

    def set_on_top(self, on_top):
        """Set always-on-top externally."""
        self._on_top = on_top
        self.on_top_check.blockSignals(True)
        self.on_top_check.setChecked(on_top)
        self.on_top_check.blockSignals(False)
        self._apply_window_flags()
        self.show()

    def set_size(self, w, h):
        """Set mini window size externally."""
        self._w = w
        self._h = h
        self.setFixedSize(w, h)

    # Draggable window support
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor, QPainterPath, QBrush
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        painter.fillPath(path, QBrush(QColor(COLORS['bg'])))
        painter.end()
