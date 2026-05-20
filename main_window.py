"""Main window for the Todo List application."""

import json
import os
import sys

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QStackedWidget, QFrame, QSizePolicy,
    QMessageBox, QToolButton, QMenu
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QCursor, QIcon, QAction

from styles import (
    COLORS,
    build_main_stylesheet,
    set_theme,
    get_theme,
    set_accent_color,
    get_accent_color,
)
from database import (
    APIUnavailableError,
    get_active_tasks, complete_task, delete_task, toggle_star,
    add_task, update_task, get_task_by_id,
    get_quick_tasks, update_task_position,
    get_board_categories, add_board_category, update_board_category,
    delete_board_category, update_task_category,
    update_board_category_positions, auto_complete_task, get_completed_tasks,
    get_sessions, revoke_sessions, get_api_token, set_api_token
)
from task_card import TaskCard
from dialogs import TaskDialog, TaskDetailDialog, LoginDialog
from history_view import HistoryView
from settings_panel import SettingsPanel
from mini_mode import MiniMode
from notes_view import NotesView
from quick_view import QuickView
from i18n import t, set_language, get_language
from kanban_view import KanbanView, CategoryDialog
from date_utils import is_overdue


def _get_data_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


PREFS_PATH = os.path.join(_get_data_dir(), "prefs.json")


def load_prefs() -> dict:
    """Load saved user preferences."""
    try:
        with open(PREFS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_prefs(prefs: dict):
    """Save user preferences."""
    with open(PREFS_PATH, "w", encoding="utf-8") as f:
        json.dump(prefs, f, indent=2)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        # Load preferences
        prefs = load_prefs()
        lang = prefs.get("language", "zh_tw")
        theme = prefs.get("theme", "light")
        accent = prefs.get("accent", "purple")
        self._opacity = prefs.get("opacity", 1.0)
        self._on_top = prefs.get("on_top", False)
        self._mini_w = prefs.get("mini_width", 200)
        self._mini_h = prefs.get("mini_height", 380)
        self._mini_view_mode = self._normalize_mini_view_mode(prefs.get("mini_view_mode", "tasks"))
        self._mini_visible_views = self._normalize_mini_visible_views(prefs.get("mini_visible_views", ["tasks", "kanban"]))
        self._mini_show_gadgets = bool(prefs.get("mini_show_gadgets", False))
        self._mini_gadget_clock = bool(prefs.get("mini_gadget_clock", True))
        self._mini_gadget_digital = bool(prefs.get("mini_gadget_digital", True))
        self._mini_clock_theme = prefs.get("mini_clock_theme", "classic")
        self._kanban_min_col_width = prefs.get("kanban_min_col_width", 260)
        self._kanban_show_quick = prefs.get("kanban_show_quick", False)
        self._kanban_auto_complete_enabled = prefs.get("kanban_auto_complete_enabled", False)
        self._kanban_auto_complete_color = prefs.get("kanban_auto_complete_color", "#D1D5DB")
        self._kanban_auto_complete_retention = int(prefs.get("kanban_auto_complete_retention_days", 3))
        self._kanban_recent_completed_enabled = prefs.get("kanban_recent_completed_enabled", False)
        self._kanban_recent_completed_days = int(prefs.get("kanban_recent_completed_days", 3))

        set_language(lang)
        set_theme(theme)
        set_accent_color(accent)

        self.setWindowTitle(t("app_title"))
        self.setMinimumSize(520, 640)
        self.resize(560, 720)
        self.setStyleSheet(build_main_stylesheet())
        self.setWindowOpacity(self._opacity)

        if self._on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        self.mini_window = None
        self._current_view = 0
        self._build_ui()
        self.refresh_tasks()
        self.refresh_quick()

    def _normalize_mini_view_mode(self, mode: str) -> str:
        mapping = {
            "list": "tasks",
            "task": "tasks",
            "tasks": "tasks",
            "quick": "quick",
            "kanban": "kanban",
            "clock": "clock",
            "big_clock": "clock",
        }
        return mapping.get(mode, "tasks")

    def _normalize_mini_visible_views(self, views) -> list[str]:
        normalized = []
        for view in views or ["tasks", "kanban"]:
            view = self._normalize_mini_view_mode(view)
            if view not in normalized:
                normalized.append(view)
        return normalized or ["tasks"]

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.header = QWidget()
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(20, 14, 20, 14)
        self.header_layout.setSpacing(12)
        main_layout.addWidget(self.header)

        self.app_title = QLabel(t("app_title"))
        self.app_title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.header_layout.addWidget(self.app_title)

        self.header_layout.addStretch()

        # Navigation buttons
        self.nav_tasks_btn = QPushButton(t("nav_tasks"))
        self.nav_tasks_btn.setObjectName("navBtn")
        self.nav_tasks_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        self.nav_tasks_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.nav_tasks_btn.clicked.connect(lambda: self._switch_view(0))
        self.header_layout.addWidget(self.nav_tasks_btn)

        self.nav_quick_btn = QPushButton(t("nav_quick"))
        self.nav_quick_btn.setObjectName("navBtn")
        self.nav_quick_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        self.nav_quick_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.nav_quick_btn.clicked.connect(lambda: self._switch_view(1))
        self.header_layout.addWidget(self.nav_quick_btn)

        self.nav_kanban_btn = QPushButton(t("nav_kanban"))
        self.nav_kanban_btn.setObjectName("navBtn")
        self.nav_kanban_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        self.nav_kanban_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.nav_kanban_btn.clicked.connect(lambda: self._switch_view(2))
        self.header_layout.addWidget(self.nav_kanban_btn)

        self.nav_history_btn = QPushButton(t("nav_history"))
        self.nav_history_btn.setObjectName("navBtn")
        self.nav_history_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        self.nav_history_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.nav_history_btn.clicked.connect(lambda: self._switch_view(3))
        self.header_layout.addWidget(self.nav_history_btn)

        self.nav_notes_btn = QPushButton(t("nav_notes"))
        self.nav_notes_btn.setObjectName("navBtn")
        self.nav_notes_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        self.nav_notes_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.nav_notes_btn.clicked.connect(lambda: self._switch_view(4))
        self.header_layout.addWidget(self.nav_notes_btn)

        self.nav_more_btn = QToolButton()
        self.nav_more_btn.setText("☰")
        self.nav_more_btn.setObjectName("navBtn")
        self.nav_more_btn.setFont(QFont("Segoe UI", 16))
        self.nav_more_btn.setFixedSize(40, 40)
        self.nav_more_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.nav_more_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.nav_more_btn.setToolTip(t("nav_more"))
        self.nav_more_btn.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                color: {COLORS['text_secondary']};
                border: none;
                border-radius: 8px;
                padding: 8px 10px;
            }}
            QToolButton:hover {{
                background-color: {COLORS['surface_hover']};
                color: {COLORS['text']};
            }}
        """)
        self.nav_menu = QMenu(self)
        self.nav_actions = {}
        self.nav_more_btn.setMenu(self.nav_menu)
        self._build_nav_menu()
        self.header_layout.addWidget(self.nav_more_btn)

        self.nav_settings_btn = QPushButton("⚙")
        self.nav_settings_btn.setObjectName("navBtn")
        self.nav_settings_btn.setFont(QFont("Segoe UI", 16))
        self.nav_settings_btn.setFixedSize(40, 40)
        self.nav_settings_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.nav_settings_btn.clicked.connect(lambda: self._switch_view(5))
        self.header_layout.addWidget(self.nav_settings_btn)

        main_layout.addWidget(self.header)

        # Stacked views
        self.stack = QStackedWidget()

        # View 0: Tasks
        self.tasks_page = QWidget()
        tasks_layout = QVBoxLayout(self.tasks_page)
        tasks_layout.setContentsMargins(16, 16, 16, 16)
        tasks_layout.setSpacing(12)

        # Task count header
        task_header = QHBoxLayout()
        self.task_count_label = QLabel(t("task_count", n=0, s="s"))
        self.task_count_label.setFont(QFont("Segoe UI", 14, QFont.Weight.DemiBold))
        self.task_count_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        task_header.addWidget(self.task_count_label)
        task_header.addStretch()

        self.add_btn = QPushButton(t("add_task"))
        self.add_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        self.add_btn.setMinimumHeight(40)
        self.add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.add_btn.clicked.connect(self._add_task)
        task_header.addWidget(self.add_btn)

        tasks_layout.addLayout(task_header)

        # Scrollable task list
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.task_container = QWidget()
        self.task_layout = QVBoxLayout(self.task_container)
        self.task_layout.setContentsMargins(0, 0, 0, 0)
        self.task_layout.setSpacing(8)
        self.task_layout.addStretch()

        self.scroll.setWidget(self.task_container)
        tasks_layout.addWidget(self.scroll)

        self.stack.addWidget(self.tasks_page)

        # View 1: Quick sticky notes
        self.quick_view = QuickView()
        self.quick_view.add_quick_requested.connect(self._add_quick)
        self.quick_view.task_completed.connect(self._complete_task)
        self.quick_view.task_deleted.connect(self._delete_task)
        self.quick_view.task_edit_requested.connect(self._show_quick_detail)
        self.quick_view.task_moved.connect(self._move_quick_card)
        self.stack.addWidget(self.quick_view)

        # View 2: Kanban
        self.kanban_view = KanbanView()
        self.kanban_view.add_category_requested.connect(self._add_category)
        self.kanban_view.add_task_requested.connect(self._add_task)
        self.kanban_view.edit_category_requested.connect(self._edit_category)
        self.kanban_view.delete_category_requested.connect(self._delete_category)
        self.kanban_view.task_moved.connect(self._move_task_to_category)
        self.kanban_view.task_completed.connect(self._complete_task)
        self.kanban_view.task_deleted.connect(self._delete_task)
        self.kanban_view.task_edit_requested.connect(self._show_task_detail)
        self.kanban_view.categories_reordered.connect(self._reorder_categories)
        self.kanban_view.show_quick_toggled.connect(self._on_kanban_show_quick_toggled)
        self.kanban_view.set_layout_preferences(self._kanban_min_col_width)
        self.kanban_view.set_show_quick(self._kanban_show_quick)
        self.stack.addWidget(self.kanban_view)

        # View 3: History
        self.history_view = HistoryView()
        self.history_view.task_deleted.connect(self._on_history_deleted)
        self.stack.addWidget(self.history_view)

        # View 4: Notes
        self.notes_view = NotesView()
        self.stack.addWidget(self.notes_view)

        # View 5: Settings (scrollable)
        self.settings_panel = SettingsPanel()
        self.settings_panel.opacity_changed.connect(self._set_opacity)
        self.settings_panel.always_on_top_changed.connect(self._set_always_on_top)
        self.settings_panel.mini_mode_requested.connect(self._enter_mini_mode)
        self.settings_panel.language_changed.connect(self._on_language_changed)
        self.settings_panel.theme_changed.connect(self._on_theme_changed)
        self.settings_panel.accent_changed.connect(self._on_accent_changed)
        self.settings_panel.mini_size_changed.connect(self._on_mini_size_changed)
        self.settings_panel.kanban_min_width_changed.connect(self._on_kanban_min_width_changed)
        self.settings_panel.kanban_auto_complete_changed.connect(self._on_kanban_auto_complete_changed)
        self.settings_panel.kanban_auto_complete_color_changed.connect(self._on_kanban_auto_complete_color_changed)
        self.settings_panel.kanban_auto_complete_days_changed.connect(self._on_kanban_auto_complete_days_changed)
        self.settings_panel.kanban_recent_completed_changed.connect(self._on_kanban_recent_completed_changed)
        self.settings_panel.kanban_recent_completed_days_changed.connect(self._on_kanban_recent_completed_days_changed)
        self.settings_panel.mini_views_changed.connect(self._on_mini_views_changed)
        self.settings_panel.mini_gadgets_changed.connect(self._on_mini_gadgets_changed)
        self.settings_panel.mini_clock_theme_changed.connect(self._on_mini_clock_theme_changed)
        self.settings_panel.session_refresh_requested.connect(self._refresh_sessions)
        self.settings_panel.session_revoke_requested.connect(self._revoke_selected_sessions)

        # Sync settings panel to current state
        self.settings_panel.opacity_slider.setValue(int(self._opacity * 100))
        self.settings_panel.on_top_check.setChecked(self._on_top)
        self.settings_panel.mini_width_spin.setValue(self._mini_w)
        self.settings_panel.mini_height_spin.setValue(self._mini_h)
        self.settings_panel.set_kanban_layout(self._kanban_min_col_width)
        self.settings_panel.set_kanban_auto_complete(
            self._kanban_auto_complete_enabled,
            self._kanban_auto_complete_color,
            self._kanban_auto_complete_retention,
        )
        self.settings_panel.set_kanban_recent_completed(
            self._kanban_recent_completed_enabled,
            self._kanban_recent_completed_days,
        )
        self.settings_panel.set_mini_visible_views(self._mini_visible_views)
        self.settings_panel.set_mini_gadgets(
            self._mini_show_gadgets,
            self._mini_gadget_clock,
            self._mini_gadget_digital,
        )
        self.settings_panel.set_clock_theme(self._mini_clock_theme)
        self.settings_panel.set_accent(get_accent_color())
        self.settings_panel.set_sessions([])

        self.settings_scroll = QScrollArea()
        self.settings_scroll.setWidgetResizable(True)
        self.settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.settings_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.settings_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.settings_scroll.setWidget(self.settings_panel)

        self.stack.addWidget(self.settings_scroll)

        main_layout.addWidget(self.stack)

        self._update_nav_style(0)

    def _build_nav_menu(self):
        self.nav_menu.clear()
        self.nav_actions.clear()
        items = [
            (0, t("nav_tasks")),
            (1, t("nav_quick")),
            (2, t("nav_kanban")),
            (3, t("nav_history")),
            (4, t("nav_notes")),
            (5, t("settings_title")),
        ]
        for index, label in items:
            action = QAction(label, self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked=False, i=index: self._switch_view(i))
            self.nav_menu.addAction(action)
            self.nav_actions[index] = action

    def _sync_nav_menu_state(self, active_index: int):
        for index, action in self.nav_actions.items():
            action.setChecked(index == active_index)

    def _update_header_navigation_mode(self):
        if not hasattr(self, "header"):
            return
        nav_buttons = [self.nav_tasks_btn, self.nav_quick_btn, self.nav_kanban_btn, self.nav_history_btn, self.nav_notes_btn]
        available = max(0, self.header.width() - self.header_layout.contentsMargins().left() - self.header_layout.contentsMargins().right())
        title_width = self.app_title.sizeHint().width()
        fixed_width = self.nav_more_btn.sizeHint().width() + self.nav_settings_btn.sizeHint().width() + 80
        nav_width = sum(btn.sizeHint().width() for btn in nav_buttons) + self.header_layout.spacing() * (len(nav_buttons) - 1)
        collapse = available < (title_width + fixed_width + nav_width)

        for btn in nav_buttons:
            btn.setVisible(not collapse)
        self.nav_more_btn.setVisible(collapse)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_header_navigation_mode()

    def _switch_view(self, index):
        self._current_view = index
        self.stack.setCurrentIndex(index)
        self._update_nav_style(index)
        self._sync_nav_menu_state(index)
        if index == 0:
            self.refresh_tasks()
        elif index == 1:
            self.refresh_quick()
        elif index == 2:
            self.refresh_kanban()
        elif index == 3:
            self.history_view.refresh()
        elif index == 4:
            self.notes_view.refresh()

    def _update_nav_style(self, active_index):
        buttons = [
            self.nav_tasks_btn,
            self.nav_quick_btn,
            self.nav_kanban_btn,
            self.nav_history_btn,
            self.nav_notes_btn,
            self.nav_settings_btn,
        ]
        for i, btn in enumerate(buttons):
            if i == active_index:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['primary']};
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 8px 16px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {COLORS['text_secondary']};
                        border: none;
                        border-radius: 8px;
                        padding: 8px 16px;
                    }}
                    QPushButton:hover {{
                        background-color: {COLORS['surface_hover']};
                        color: {COLORS['text']};
                    }}
                """)

    def refresh_tasks(self):
        """Reload active tasks from the database."""
        # Clear existing cards
        while self.task_layout.count() > 1:
            item = self.task_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tasks = get_active_tasks()
        count = len(tasks)
        self.task_count_label.setText(t("task_count", n=count, s="" if count == 1 else "s"))

        if not tasks:
            empty_label = QLabel(t("no_tasks"))
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setFont(QFont("Segoe UI", 14))
            empty_label.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 40px;")
            self.task_layout.insertWidget(0, empty_label)
            return

        for task in tasks:
            card = TaskCard(task)
            card.completed.connect(self._complete_task)
            card.deleted.connect(self._delete_task)
            card.starred.connect(self._toggle_star)
            card.double_clicked.connect(self._show_task_detail)
            self.task_layout.insertWidget(self.task_layout.count() - 1, card)

    def _add_task(self, category_id=None):
        if category_id == "__quick__":
            self._add_quick()
            return
        dlg = TaskDialog(self, default_category_id=category_id)
        if dlg.exec() and dlg.result_data:
            data = dlg.result_data
            add_task(
                title=data["title"],
                description=data["description"],
                due_date=data["due_date"],
                is_starred=data["is_starred"],
                category_id=data.get("category_id"),
                color=data.get("color", ""),
                task_type="task",
            )
            self.refresh_tasks()
            self.refresh_quick()
            self.refresh_kanban()

    def _add_quick(self):
        dlg = TaskDialog(self, task_kind="quick")
        if dlg.exec() and dlg.result_data:
            data = dlg.result_data
            add_task(
                title=data["title"],
                description=data["description"],
                due_date=data["due_date"],
                is_starred=data["is_starred"],
                category_id=None,
                color=data.get("color", ""),
                task_type="quick",
            )
            self.refresh_quick()
            self.refresh_kanban()

    def _complete_task(self, task_id):
        complete_task(task_id)
        self.refresh_tasks()
        self.refresh_quick()
        self.refresh_kanban()

    def _delete_task(self, task_id):
        reply = QMessageBox.question(
            self, t("delete_title"),
            t("delete_confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_task(task_id)
            self.refresh_tasks()
            self.refresh_quick()
            self.refresh_kanban()

    def _toggle_star(self, task_id):
        toggle_star(task_id)
        self.refresh_tasks()
        self.refresh_quick()
        self.refresh_kanban()

    def _show_task_detail(self, task_id):
        task = get_task_by_id(task_id)
        if task:
            task_kind = "quick" if task.get("task_type") == "quick" else "task"
            dlg = TaskDialog(self, task=task, task_kind=task_kind)
            if dlg.exec() and dlg.result_data:
                data = dlg.result_data
                update_task(
                    task_id,
                    title=data["title"],
                    description=data["description"],
                    due_date=data["due_date"],
                    is_starred=data["is_starred"],
                    category_id=data.get("category_id"),
                    color=data.get("color", ""),
                    task_type=task.get("task_type") or "task",
                )
                self.refresh_tasks()
                self.refresh_quick()
                self.refresh_kanban()

    def _show_quick_detail(self, task_id):
        task = get_task_by_id(task_id)
        if task:
            dlg = TaskDialog(self, task=task, task_kind="quick")
            if dlg.exec() and dlg.result_data:
                data = dlg.result_data
                update_task(
                    task_id,
                    title=data["title"],
                    description=data["description"],
                    due_date=data["due_date"],
                    is_starred=data["is_starred"],
                    category_id=None,
                    color=data.get("color", ""),
                    task_type="quick",
                )
                self.refresh_quick()
                self.refresh_kanban()

    def _move_quick_card(self, task_id: int, x: int, y: int):
        update_task_position(task_id, x, y)

    def refresh_quick(self):
        quick_tasks = get_quick_tasks()
        self.quick_view.refresh(quick_tasks)

    def refresh_kanban(self):
        tasks = get_active_tasks(include_quick=self._kanban_show_quick)

        auto_complete_candidates = []
        if self._kanban_auto_complete_enabled:
            for task in tasks:
                if task.get("due_date") and is_overdue(task.get("due_date")):
                    auto_complete_candidates.append(task)

            for task in auto_complete_candidates:
                try:
                    auto_complete_task(int(task["id"]))
                except APIUnavailableError:
                    pass

            if auto_complete_candidates:
                tasks = get_active_tasks(include_quick=self._kanban_show_quick)

        categories = get_board_categories()

        auto_completed_recent = []
        if self._kanban_auto_complete_enabled:
            completed = get_completed_tasks()
            from datetime import datetime, timedelta
            cutoff = datetime.now() - timedelta(days=int(self._kanban_auto_complete_retention))
            for completed_task in completed:
                auto_completed_at = completed_task.get("auto_completed_at")
                if not auto_completed_at:
                    continue
                try:
                    auto_completed_at_dt = datetime.fromisoformat(str(auto_completed_at).replace("Z", "+00:00"))
                    if auto_completed_at_dt.tzinfo is not None:
                        auto_completed_at_dt = auto_completed_at_dt.replace(tzinfo=None)
                except Exception:
                    try:
                        auto_completed_at_dt = datetime.strptime(str(auto_completed_at), "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        continue
                if auto_completed_at_dt >= cutoff:
                    auto_completed_recent.append(completed_task)

        recent_completed = []
        if self._kanban_recent_completed_enabled:
            completed = get_completed_tasks()
            from datetime import datetime, timedelta
            cutoff = datetime.now() - timedelta(days=int(self._kanban_recent_completed_days))
            for completed_task in completed:
                completed_at = completed_task.get("completed_at")
                if not completed_at:
                    continue
                try:
                    completed_at_dt = datetime.fromisoformat(str(completed_at).replace("Z", "+00:00"))
                    if completed_at_dt.tzinfo is not None:
                        completed_at_dt = completed_at_dt.replace(tzinfo=None)
                except Exception:
                    try:
                        completed_at_dt = datetime.strptime(str(completed_at), "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        continue
                if completed_at_dt >= cutoff:
                    completed_task["recent_completed"] = True
                    recent_completed.append(completed_task)

        self.kanban_view.refresh(
            tasks,
            categories,
            recent_completed=recent_completed,
            auto_complete_tasks=auto_completed_recent,
            auto_complete_color=self._kanban_auto_complete_color,
        )

    def _on_kanban_show_quick_toggled(self, enabled: bool):
        self._kanban_show_quick = bool(enabled)
        self._save_current_prefs()
        self.refresh_kanban()

    def _on_mini_views_changed(self, views: list[str]):
        self._mini_visible_views = self._normalize_mini_visible_views(views)
        if self._mini_view_mode not in self._mini_visible_views:
            self._mini_view_mode = self._mini_visible_views[0]
        self._save_current_prefs()
        if self.mini_window:
            self.mini_window.set_visible_views(self._mini_visible_views)
            self.mini_window.set_view_mode(self._mini_view_mode)

    def _on_mini_gadgets_changed(self, enabled: bool, show_clock: bool, show_digital: bool):
        self._mini_show_gadgets = bool(enabled)
        self._mini_gadget_clock = bool(show_clock)
        self._mini_gadget_digital = bool(show_digital)
        if self._mini_show_gadgets and not (self._mini_gadget_clock or self._mini_gadget_digital):
            self._mini_gadget_clock = True
        self._save_current_prefs()
        if self.mini_window:
            self.mini_window.set_gadget_settings(
                self._mini_show_gadgets,
                self._mini_gadget_clock,
                self._mini_gadget_digital,
            )

    def _on_mini_clock_theme_changed(self, clock_theme: str):
        self._mini_clock_theme = clock_theme
        self._save_current_prefs()
        if self.mini_window:
            self.mini_window.set_clock_theme(self._mini_clock_theme)

    def _add_category(self):
        dlg = CategoryDialog(self)
        if dlg.exec() and dlg.result_data:
            data = dlg.result_data
            add_board_category(data["name"], data.get("color", ""))
            self.refresh_kanban()

    def _edit_category(self, category_id: int):
        category = None
        for cat in get_board_categories():
            if cat["id"] == category_id:
                category = cat
                break
        if not category:
            return
        dlg = CategoryDialog(self, category=category)
        if dlg.exec() and dlg.result_data:
            data = dlg.result_data
            update_board_category(category_id, data["name"], data.get("color", ""))
            self.refresh_kanban()

    def _delete_category(self, category_id: int):
        if self.kanban_view.confirm_delete_category():
            delete_board_category(category_id)
            self.refresh_tasks()
            self.refresh_kanban()

    def _move_task_to_category(self, task_id: int, category_id):
        task = get_task_by_id(task_id)
        if task and (task.get("task_type") == "quick"):
            return
        update_task_category(task_id, category_id)
        self.refresh_tasks()
        self.refresh_quick()
        self.refresh_kanban()

    def _reorder_categories(self, ordered_ids: list[int]):
        update_board_category_positions(ordered_ids)
        self.refresh_kanban()

    def _on_kanban_min_width_changed(self, min_col_width: int):
        self._kanban_min_col_width = int(min_col_width)
        self.kanban_view.set_layout_preferences(self._kanban_min_col_width)
        self._save_current_prefs()

    def _on_kanban_auto_complete_changed(self, enabled: bool):
        self._kanban_auto_complete_enabled = bool(enabled)
        self._save_current_prefs()
        self.refresh_kanban()

    def _on_kanban_auto_complete_color_changed(self, color: str):
        self._kanban_auto_complete_color = color or "#D1D5DB"
        self._save_current_prefs()
        self.refresh_kanban()

    def _on_kanban_auto_complete_days_changed(self, days: int):
        try:
            self._kanban_auto_complete_retention = int(days)
        except Exception:
            self._kanban_auto_complete_retention = 3
        self._save_current_prefs()
        self.refresh_kanban()

    def _on_kanban_recent_completed_changed(self, enabled: bool):
        self._kanban_recent_completed_enabled = bool(enabled)
        self._save_current_prefs()
        self.refresh_kanban()

    def _on_kanban_recent_completed_days_changed(self, days: int):
        try:
            self._kanban_recent_completed_days = int(days)
        except Exception:
            self._kanban_recent_completed_days = 3
        self._save_current_prefs()
        self.refresh_kanban()

    def _on_history_deleted(self):
        """Refresh calendar after a completed task is deleted from history."""
        self.history_view.calendar_view.refresh()

    def _set_opacity(self, opacity):
        self._opacity = opacity
        self.setWindowOpacity(opacity)
        self._save_current_prefs()

    def _set_always_on_top(self, enabled):
        self._on_top = enabled
        flags = self.windowFlags()
        if enabled:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()
        self._save_current_prefs()

    def _enter_mini_mode(self):
        self.hide()
        if self.mini_window is None:
            self.mini_window = MiniMode(
                opacity=self._opacity, on_top=self._on_top,
                width=self._mini_w, height=self._mini_h,
                view_mode=self._mini_view_mode,
                visible_views=self._mini_visible_views,
                show_gadgets=self._mini_show_gadgets,
                show_gadget_clock=self._mini_gadget_clock,
                show_gadget_digital=self._mini_gadget_digital,
                clock_theme=self._mini_clock_theme,
            )
            self.mini_window.restore_requested.connect(self._exit_mini_mode)
            self.mini_window.view_mode_changed.connect(self._on_mini_view_mode_changed)
        else:
            self.mini_window.set_opacity(self._opacity)
            self.mini_window.set_on_top(self._on_top)
            self.mini_window.set_size(self._mini_w, self._mini_h)
            self.mini_window.set_visible_views(self._mini_visible_views)
            self.mini_window.set_gadget_settings(
                self._mini_show_gadgets,
                self._mini_gadget_clock,
                self._mini_gadget_digital,
            )
            self.mini_window.set_clock_theme(self._mini_clock_theme)
            self.mini_window.set_view_mode(self._mini_view_mode)
        self.mini_window.refresh()
        self.mini_window.show()

    def _exit_mini_mode(self):
        if self.mini_window:
            self.mini_window.hide()
        self.show()
        self.refresh_tasks()
        self.refresh_kanban()

    def _on_mini_size_changed(self, w, h):
        self._mini_w = w
        self._mini_h = h
        self._save_current_prefs()
        if self.mini_window:
            self.mini_window.set_size(w, h)

    def _on_mini_view_mode_changed(self, mode: str):
        self._mini_view_mode = self._normalize_mini_view_mode(mode)
        self._save_current_prefs()

    # --- Theme / Language ---
    def _on_language_changed(self, lang):
        set_language(lang)
        self._save_current_prefs()
        self._rebuild_ui()

    def _on_theme_changed(self, theme):
        set_theme(theme)
        self._save_current_prefs()
        self._rebuild_ui()

    def _on_accent_changed(self, accent: str):
        set_accent_color(accent)
        self._save_current_prefs()
        self._rebuild_ui()

    def _rebuild_ui(self):
        """Rebuild the entire UI after theme or language change."""
        # Preserve current view
        view_idx = self._current_view
        opacity_val = self.settings_panel.opacity_slider.value()
        on_top_val = self.settings_panel.on_top_check.isChecked()

        # Re-apply stylesheet
        self.setStyleSheet(build_main_stylesheet())
        self.setWindowTitle(t("app_title"))

        # Update header text
        self.app_title.setText(t("app_title"))
        self.nav_tasks_btn.setText(t("nav_tasks"))
        self.nav_quick_btn.setText(t("nav_quick"))
        self.nav_kanban_btn.setText(t("nav_kanban"))
        self.nav_history_btn.setText(t("nav_history"))
        self.nav_notes_btn.setText(t("nav_notes"))
        self.nav_more_btn.setText("☰")
        self.nav_more_btn.setToolTip(t("nav_more"))
        self.add_btn.setText(t("add_task"))

        # Update sub-panels
        self.settings_panel.retranslate()
        self.history_view.retranslate()
        self.notes_view.retranslate()
        self.quick_view.retranslate()
        self.kanban_view.retranslate()
        if self.mini_window:
            self.mini_window.retranslate()
        self._build_nav_menu()

        # Update nav style
        self._update_nav_style(view_idx)
        self._sync_nav_menu_state(view_idx)
        self._update_header_navigation_mode()

        # Refresh content
        self.refresh_tasks()
        self.refresh_quick()
        self.refresh_kanban()
        self.history_view.refresh()

        # Destroy and recreate mini window on next use
        if self.mini_window:
            self.mini_window.close()
            self.mini_window = None

        self.kanban_view.set_layout_preferences(self._kanban_min_col_width)

    def _refresh_sessions(self):
        self.settings_panel.set_sessions(get_sessions())

    def _revoke_selected_sessions(self, session_ids: list[int]):
        if not session_ids:
            return
        try:
            result = revoke_sessions(session_ids)
        except APIUnavailableError:
            return
        current_token = get_api_token()
        revoked_ids = result.get("revoked_ids", []) or []
        if result.get("revoked_current") or (current_token and current_token in revoked_ids):
            set_api_token(None)
            login_dialog = LoginDialog(self)
            login_dialog.status_label.setText(t("backend_unavailable"))
            login_dialog.exec()
        self._refresh_sessions()

    def _save_current_prefs(self):
        save_prefs({
            "language": get_language(),
            "theme": get_theme(),
            "accent": get_accent_color(),
            "opacity": self._opacity,
            "on_top": self._on_top,
            "mini_width": self._mini_w,
            "mini_height": self._mini_h,
            "mini_view_mode": self._mini_view_mode,
            "mini_visible_views": self._mini_visible_views,
            "mini_show_gadgets": self._mini_show_gadgets,
            "mini_gadget_clock": self._mini_gadget_clock,
            "mini_gadget_digital": self._mini_gadget_digital,
            "mini_clock_theme": self._mini_clock_theme,
            "kanban_min_col_width": self._kanban_min_col_width,
            "kanban_show_quick": self._kanban_show_quick,
            "kanban_auto_complete_enabled": self._kanban_auto_complete_enabled,
            "kanban_auto_complete_color": self._kanban_auto_complete_color,
            "kanban_auto_complete_retention_days": self._kanban_auto_complete_retention,
            "kanban_recent_completed_enabled": self._kanban_recent_completed_enabled,
            "kanban_recent_completed_days": self._kanban_recent_completed_days,
        })
