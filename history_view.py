"""History view with list mode and calendar mode for completed tasks."""

import calendar
from datetime import date, datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout, QTabWidget, QSizePolicy,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from styles import COLORS
from database import get_completed_tasks, get_tasks_for_month, get_task_by_id, delete_task
from date_utils import format_datetime, format_due_date
from task_card import CompletedTaskCard
from dialogs import TaskDialog
from i18n import t


class HistoryListView(QWidget):
    """List view of completed tasks."""

    task_deleted = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 8, 0, 8)
        self.container_layout.setSpacing(8)
        self.container_layout.addStretch()

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

    def refresh(self):
        # Clear
        while self.container_layout.count() > 1:
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tasks = get_completed_tasks()

        if not tasks:
            empty_label = QLabel(t("no_completed_tasks"))
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setFont(QFont("Segoe UI", 14))
            empty_label.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 40px;")
            self.container_layout.insertWidget(0, empty_label)
            return

        for task in tasks:
            card = CompletedTaskCard(task)
            card.double_clicked.connect(self._show_detail)
            card.deleted.connect(self._on_delete)
            self.container_layout.insertWidget(self.container_layout.count() - 1, card)

    def _show_detail(self, task_id):
        task = get_task_by_id(task_id)
        if task:
            from database import update_task
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
                self.refresh()

    def _on_delete(self, task_id):
        reply = QMessageBox.question(
            self, t("delete_completed_title"),
            t("delete_completed_confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_task(task_id)
            self.refresh()
            self.task_deleted.emit()


class CalendarView(QWidget):
    """Monthly calendar grid view showing tasks."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_year = date.today().year
        self.current_month = date.today().month
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(12)

        # Navigation
        nav = QHBoxLayout()
        nav.setSpacing(12)

        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedSize(36, 36)
        self.prev_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['surface']};
                color: {COLORS['text']};
                border: none;
                border-radius: 18px;
                font-size: 14px;
            }}
            QPushButton:hover {{ background: {COLORS['surface_hover']}; }}
        """)
        self.prev_btn.clicked.connect(self._prev_month)
        nav.addWidget(self.prev_btn)

        self.month_label = QLabel()
        self.month_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav.addWidget(self.month_label, 1)

        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedSize(36, 36)
        self.next_btn.setStyleSheet(self.prev_btn.styleSheet())
        self.next_btn.clicked.connect(self._next_month)
        nav.addWidget(self.next_btn)

        layout.addLayout(nav)

        # Scroll area for grid
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(4)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll.setWidget(self.grid_container)
        layout.addWidget(self.scroll)

    def _prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.refresh()

    def _next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.refresh()

    def refresh(self):
        self.month_label.setText(f"{self.current_year} / {self.current_month:02d}")

        # Clear grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Day headers
        day_keys = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        for i, key in enumerate(day_keys):
            lbl = QLabel(t(key))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            lbl.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 4px;")
            self.grid_layout.addWidget(lbl, 0, i)

        # Get tasks for this month
        tasks = get_tasks_for_month(self.current_year, self.current_month)

        # Organize tasks by day
        task_by_day: dict[int, list] = {}
        for tk in tasks:
            dd = tk.get("due_date")
            ca = tk.get("completed_at")
            if dd:
                try:
                    d = date.fromisoformat(dd[:10])
                    if d.year == self.current_year and d.month == self.current_month:
                        task_by_day.setdefault(d.day, []).append(tk)
                except ValueError:
                    pass
            if ca:
                try:
                    dt = datetime.fromisoformat(ca)
                    if dt.year == self.current_year and dt.month == self.current_month:
                        day = dt.day
                        if day not in task_by_day or tk not in task_by_day[day]:
                            task_by_day.setdefault(day, []).append(tk)
                except ValueError:
                    pass

        # Build calendar grid
        cal = calendar.monthcalendar(self.current_year, self.current_month)
        today = date.today()

        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                cell = QFrame()
                cell.setMinimumSize(70, 70)
                cell_layout = QVBoxLayout(cell)
                cell_layout.setContentsMargins(4, 4, 4, 4)
                cell_layout.setSpacing(2)

                if day == 0:
                    cell.setStyleSheet(f"background: transparent; border-radius: 8px;")
                else:
                    is_today = (day == today.day and self.current_month == today.month
                                and self.current_year == today.year)
                    bg = COLORS['primary'] if is_today else COLORS['surface']
                    cell.setStyleSheet(f"""
                        QFrame {{
                            background: {bg};
                            border-radius: 8px;
                            border: 1px solid {COLORS['border']};
                        }}
                    """)

                    day_label = QLabel(str(day))
                    day_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                    day_label.setAlignment(Qt.AlignmentFlag.AlignRight)
                    if is_today:
                        day_label.setStyleSheet("color: white;")
                    cell_layout.addWidget(day_label)

                    # Tasks for this day
                    day_tasks = task_by_day.get(day, [])
                    for dt_task in day_tasks[:2]:  # Show max 2
                        task_lbl = QLabel(dt_task["title"][:12])
                        task_lbl.setFont(QFont("Segoe UI", 8))
                        status = dt_task.get("status", "active")
                        color = COLORS['success'] if status == "completed" else COLORS['accent']
                        task_lbl.setStyleSheet(f"color: {color}; background: transparent;")
                        cell_layout.addWidget(task_lbl)

                    if len(day_tasks) > 2:
                        more_lbl = QLabel(t("more_tasks", n=len(day_tasks) - 2))
                        more_lbl.setFont(QFont("Segoe UI", 8))
                        more_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
                        cell_layout.addWidget(more_lbl)

                cell_layout.addStretch()
                self.grid_layout.addWidget(cell, row_idx + 1, col_idx)


class HistoryView(QWidget):
    """Combined history view with tabs for List and Calendar modes."""

    task_deleted = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.list_view = HistoryListView()
        self.calendar_view = CalendarView()

        self.list_view.task_deleted.connect(self.task_deleted.emit)

        self.tabs.addTab(self.list_view, t("tab_list"))
        self.tabs.addTab(self.calendar_view, t("tab_calendar"))

        layout.addWidget(self.tabs)

    def refresh(self):
        self.list_view.refresh()
        self.calendar_view.refresh()

    def retranslate(self):
        """Update tab titles after language change."""
        self.tabs.setTabText(0, t("tab_list"))
        self.tabs.setTabText(1, t("tab_calendar"))
