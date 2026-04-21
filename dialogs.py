"""Add/Edit Task Dialog for the Todo List application."""

from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QCheckBox, QPushButton, QFrame, QCalendarWidget, QColorDialog
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from styles import COLORS, build_main_stylesheet
from date_utils import parse_due_date, format_due_date
from i18n import t


TASK_PRESET_COLORS = [
    "#0EA5E9", "#10B981", "#F59E0B", "#F97316", "#EF4444", "#8B5CF6", "#EC4899", "#64748B"
]


class DatePickerDialog(QDialog):
    """Popup dialog for selecting a due date."""

    def __init__(self, parent=None, initial_date: Optional[str] = None):
        super().__init__(parent)
        self.selected_date = None
        self.setWindowTitle(t("pick_date"))
        self.setFixedSize(360, 360)
        self.setStyleSheet(build_main_stylesheet())
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        if initial_date:
            try:
                from datetime import date as _date
                d = _date.fromisoformat(initial_date[:10])
                self.calendar.setSelectedDate(QDate(d.year, d.month, d.day))
            except (TypeError, ValueError):
                pass
        layout.addWidget(self.calendar)

        row = QHBoxLayout()
        cancel_btn = QPushButton(t("cancel"))
        cancel_btn.setObjectName("ghostBtn")
        cancel_btn.clicked.connect(self.reject)
        row.addWidget(cancel_btn)

        ok_btn = QPushButton(t("save"))
        ok_btn.clicked.connect(self._on_ok)
        row.addWidget(ok_btn)
        layout.addLayout(row)

    def _on_ok(self):
        qdate = self.calendar.selectedDate()
        self.selected_date = f"{qdate.year():04d}-{qdate.month():02d}-{qdate.day():02d}"
        self.accept()


class TaskDialog(QDialog):
    """Modal dialog for adding or editing a task."""

    def __init__(self, parent=None, task=None, default_category_id=None):
        super().__init__(parent)
        self.task = task
        self.result_data = None
        self._selected_color = ""
        self._default_category_id = default_category_id
        self.setWindowTitle(t("edit_task") if task else t("new_task"))
        self.setFixedSize(440, 660)
        self.setStyleSheet(build_main_stylesheet())
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._build_ui()
        if task:
            self._populate(task)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        # Header
        header = QLabel(t("edit_task") if self.task else t("new_task"))
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {COLORS['text']};")
        layout.addWidget(header)

        # Title
        title_label = QLabel(t("title_required"))
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        title_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(title_label)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText(t("title_placeholder"))
        self.title_input.setMinimumHeight(40)
        layout.addWidget(self.title_input)

        # Description
        desc_label = QLabel(t("description"))
        desc_label.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        desc_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(desc_label)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText(t("desc_placeholder"))
        self.desc_input.setMaximumHeight(80)
        layout.addWidget(self.desc_input)

        # Due date
        date_label = QLabel(t("due_date"))
        date_label.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        date_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(date_label)

        date_row = QHBoxLayout()
        date_row.setSpacing(8)

        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText(t("date_placeholder"))
        self.date_input.setMinimumHeight(40)
        date_row.addWidget(self.date_input)

        self.cal_btn = QPushButton("📅")
        self.cal_btn.setFixedSize(40, 40)
        self.cal_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cal_btn.setToolTip(t("pick_date"))
        self.cal_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['primary']};
                background-color: {COLORS['surface_hover']};
            }}
        """)
        self.cal_btn.clicked.connect(self._toggle_calendar)
        date_row.addWidget(self.cal_btn)

        layout.addLayout(date_row)

        # Starred checkbox
        self.star_check = QCheckBox(t("mark_important"))
        self.star_check.setFont(QFont("Segoe UI", 12))
        layout.addWidget(self.star_check)

        # Task color
        color_label = QLabel(t("task_color"))
        color_label.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        color_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(color_label)

        color_row = QHBoxLayout()
        color_row.setSpacing(8)

        self.color_btns = []
        for color in TASK_PRESET_COLORS:
            btn = QPushButton()
            btn.setCheckable(True)
            btn.setFixedSize(22, 22)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    border: 2px solid transparent;
                    border-radius: 11px;
                }}
                QPushButton:checked {{
                    border-color: {COLORS['text']};
                }}
            """)
            btn.clicked.connect(lambda checked=False, c=color: self._select_color(c))
            color_row.addWidget(btn)
            self.color_btns.append((btn, color))

        self.custom_color_btn = QPushButton(t("task_color_custom"))
        self.custom_color_btn.setObjectName("ghostBtn")
        self.custom_color_btn.clicked.connect(self._pick_custom_color)
        color_row.addWidget(self.custom_color_btn)

        self.clear_color_btn = QPushButton(t("task_color_none"))
        self.clear_color_btn.setObjectName("ghostBtn")
        self.clear_color_btn.clicked.connect(lambda: self._select_color(""))
        color_row.addWidget(self.clear_color_btn)

        color_row.addStretch()
        layout.addLayout(color_row)

        self.color_preview = QLabel(t("task_color_current", c=t("task_color_none")))
        self.color_preview.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(self.color_preview)

        self._sync_color_checks()
        self._update_color_preview()

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = QPushButton(t("cancel"))
        cancel_btn.setObjectName("ghostBtn")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self.save_btn = QPushButton(t("save") if self.task else t("add_task"))
        self.save_btn.setMinimumHeight(40)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    def _populate(self, task):
        self.title_input.setText(task.get("title", ""))
        self.desc_input.setPlainText(task.get("description", ""))
        due_date = task.get("due_date")
        if due_date:
            self.date_input.setText(due_date.replace("-", "/"))
        self.star_check.setChecked(bool(task.get("is_starred", 0)))
        self._selected_color = task.get("color") or ""
        self._sync_color_checks()
        self._update_color_preview()

    def _pick_custom_color(self):
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            self._select_color(color.name())

    def _select_color(self, color: str):
        self._selected_color = color
        self._sync_color_checks()
        self._update_color_preview()

    def _sync_color_checks(self):
        for btn, color in self.color_btns:
            btn.blockSignals(True)
            btn.setChecked(self._selected_color.lower() == color.lower())
            btn.blockSignals(False)

    def _update_color_preview(self):
        text = self._selected_color or t("task_color_none")
        self.color_preview.setText(t("task_color_current", c=text))
        color = self._selected_color or COLORS['border']
        self.color_preview.setStyleSheet(
            f"color: {COLORS['text_muted']}; border-left: 8px solid {color}; padding-left: 8px;"
        )

    def _toggle_calendar(self):
        """Open date picker popup dialog and apply selected date."""
        current_iso = parse_due_date(self.date_input.text())
        dlg = DatePickerDialog(self, initial_date=current_iso)
        if dlg.exec() and dlg.selected_date:
            y, m, d = dlg.selected_date.split("-")
            self.date_input.setText(f"{y}/{m}/{d}")

    def _on_save(self):
        title = self.title_input.text().strip()
        if not title:
            self.title_input.setStyleSheet(f"""
                border: 2px solid {COLORS['danger']};
                border-radius: 8px;
                padding: 8px 12px;
                background-color: {COLORS['surface']};
                color: {COLORS['text']};
            """)
            self.title_input.setFocus()
            return

        due_date = parse_due_date(self.date_input.text())
        self.result_data = {
            "title": title,
            "description": self.desc_input.toPlainText().strip(),
            "due_date": due_date,
            "is_starred": self.star_check.isChecked(),
            "category_id": self.task.get("category_id") if self.task else self._default_category_id,
            "color": self._selected_color,
        }
        self.accept()


class TaskDetailDialog(QDialog):
    """Dialog for viewing task details (read-only)."""

    def __init__(self, task: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("task_details"))
        self.setFixedSize(440, 380)
        self.setStyleSheet(build_main_stylesheet())
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._build_ui(task)

    def _build_ui(self, task):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        # Title
        title_label = QLabel(task["title"])
        title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']};")
        layout.addWidget(sep)

        # Status
        status = task.get("status", "active")
        status_display = t("status_completed") if status == "completed" else t("status_active")
        starred = t("important") if task.get("is_starred") else ""
        status_text = t("status_label", s=status_display)
        if starred:
            status_text += f"  |  {starred}"
        status_label = QLabel(status_text)
        status_label.setFont(QFont("Segoe UI", 12))
        status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(status_label)

        # Due date
        from date_utils import format_due_date, format_datetime
        due_label = QLabel(t("due_label", d=format_due_date(task.get('due_date'))))
        due_label.setFont(QFont("Segoe UI", 12))
        due_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(due_label)

        # Created
        created = format_datetime(task.get("created_at"))
        if created:
            created_label = QLabel(t("created_label", t=created))
            created_label.setFont(QFont("Segoe UI", 11))
            created_label.setStyleSheet(f"color: {COLORS['text_muted']};")
            layout.addWidget(created_label)

        # Completed at
        completed = format_datetime(task.get("completed_at"))
        if completed:
            comp_label = QLabel(t("completed_at_label", t=completed))
            comp_label.setFont(QFont("Segoe UI", 11))
            comp_label.setStyleSheet(f"color: {COLORS['success']};")
            layout.addWidget(comp_label)

        # Description
        desc = task.get("description", "")
        if desc:
            desc_header = QLabel(t("description"))
            desc_header.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
            desc_header.setStyleSheet(f"color: {COLORS['text_secondary']};")
            layout.addWidget(desc_header)

            desc_label = QLabel(desc)
            desc_label.setFont(QFont("Segoe UI", 12))
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        layout.addStretch()

        close_btn = QPushButton(t("close"))
        close_btn.setObjectName("ghostBtn")
        close_btn.setMinimumHeight(40)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
