"""Task card widget for the Todo List application."""

from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QCheckBox, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QCursor

from styles import COLORS, build_task_card_style
from date_utils import format_due_date, is_overdue, days_until
from i18n import t


class TaskCard(QFrame):
    """A single task card widget."""

    completed = pyqtSignal(int)
    deleted = pyqtSignal(int)
    starred = pyqtSignal(int)
    double_clicked = pyqtSignal(int)

    def __init__(self, task: dict, parent=None):
        super().__init__(parent)
        self.task = task
        self.task_id = task["id"]
        self.setObjectName("taskCard")
        self._apply_card_style()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(64)
        self._build_ui()

    def _apply_card_style(self):
        accent = self.task.get("color") or COLORS['border']
        self.setStyleSheet(
            build_task_card_style()
            + f"""
            QFrame#taskCard {{
                border-left: 4px solid {accent};
            }}
            """
        )

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setFixedSize(24, 24)
        self.checkbox.stateChanged.connect(self._on_complete)
        layout.addWidget(self.checkbox)

        # Star button
        self.star_btn = QPushButton()
        self.star_btn.setFixedSize(28, 28)
        self.star_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._update_star_style()
        self.star_btn.clicked.connect(self._on_star)
        layout.addWidget(self.star_btn)

        # Title + due date area
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        self.title_label = QLabel(self.task["title"])
        title_font = QFont("Segoe UI", 13, QFont.Weight.DemiBold)
        self.title_label.setFont(title_font)
        self.title_label.setWordWrap(True)
        info_layout.addWidget(self.title_label)

        # Due date
        due_text = format_due_date(self.task.get("due_date"))
        days = days_until(self.task.get("due_date"))
        if days is not None:
            if days < 0:
                due_text += f"  ({t('overdue_by', n=abs(days), s='s' if abs(days)!=1 else '')})"
            elif days == 0:
                due_text += f"  ({t('today')})"
            elif days == 1:
                due_text += f"  ({t('tomorrow')})"
            else:
                due_text += f"  ({t('days_left', n=days)})"

        self.due_label = QLabel(due_text)
        due_font = QFont("Segoe UI", 11)
        self.due_label.setFont(due_font)

        if is_overdue(self.task.get("due_date")):
            self.due_label.setStyleSheet(f"color: {COLORS['overdue']};")
        elif self.task.get("due_date"):
            self.due_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        else:
            self.due_label.setStyleSheet(f"color: {COLORS['text_muted']};")

        info_layout.addWidget(self.due_label)
        layout.addLayout(info_layout, 1)

        # Delete button
        self.delete_btn = QPushButton("✕")
        self.delete_btn.setObjectName("dangerBtn")
        self.delete_btn.setFixedSize(32, 32)
        self.delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_muted']};
                border: none;
                border-radius: 16px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['danger']};
                color: white;
            }}
        """)
        self.delete_btn.clicked.connect(self._on_delete)
        layout.addWidget(self.delete_btn)

    def _update_star_style(self):
        is_starred = self.task.get("is_starred", 0)
        if is_starred:
            self.star_btn.setText("★")
            self.star_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {COLORS['star_active']};
                    border: none;
                    font-size: 20px;
                }}
                QPushButton:hover {{
                    color: {COLORS['accent_hover']};
                }}
            """)
        else:
            self.star_btn.setText("☆")
            self.star_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {COLORS['star_inactive']};
                    border: none;
                    font-size: 20px;
                }}
                QPushButton:hover {{
                    color: {COLORS['star_active']};
                }}
            """)

    def _on_complete(self, state):
        if state:
            self.completed.emit(self.task_id)

    def _on_delete(self):
        self.deleted.emit(self.task_id)

    def _on_star(self):
        self.starred.emit(self.task_id)

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self.task_id)
        super().mouseDoubleClickEvent(event)


class CompletedTaskCard(QFrame):
    """A card for displaying completed tasks in history."""

    double_clicked = pyqtSignal(int)
    deleted = pyqtSignal(int)

    def __init__(self, task: dict, parent=None):
        super().__init__(parent)
        self.task = task
        self.task_id = task["id"]
        self.setObjectName("taskCard")
        self.setStyleSheet(f"""
            QFrame#taskCard {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(56)
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        # Checkmark
        check_label = QLabel("✓")
        check_label.setFixedSize(24, 24)
        check_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        check_label.setStyleSheet(f"""
            color: {COLORS['success']};
            font-size: 16px;
            font-weight: bold;
        """)
        layout.addWidget(check_label)

        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        title_label = QLabel(self.task["title"])
        title_label.setFont(QFont("Segoe UI", 12))
        title_label.setStyleSheet(f"color: {COLORS['text_muted']}; text-decoration: line-through;")
        info_layout.addWidget(title_label)

        from date_utils import format_datetime
        completed_text = format_datetime(self.task.get("completed_at"))
        if completed_text:
            completed_label = QLabel(t("completed_label", t=completed_text))
            completed_label.setFont(QFont("Segoe UI", 10))
            completed_label.setStyleSheet(f"color: {COLORS['text_muted']};")
            info_layout.addWidget(completed_label)

        layout.addLayout(info_layout, 1)

        # Delete button
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(28, 28)
        del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_muted']};
                border: none;
                border-radius: 14px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['danger']};
                color: white;
            }}
        """)
        del_btn.clicked.connect(lambda: self.deleted.emit(self.task_id))
        layout.addWidget(del_btn)

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self.task_id)
        super().mouseDoubleClickEvent(event)
