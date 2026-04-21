"""Database layer for the Todo List application using SQLite3."""

import sqlite3
import os
import sys
from datetime import datetime
from typing import Optional


def _get_data_dir() -> str:
    """Return the directory where persistent data files (db, prefs) should live.

    When running as a PyInstaller-bundled exe, __file__ resolves inside the
    temporary _MEIPASS folder — so we use the directory of the executable
    instead, ensuring the database is stored next to the .exe.
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


DB_PATH = os.path.join(_get_data_dir(), "todo.db")


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)


def get_connection():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize the database schema."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            due_date DATE,
            is_starred INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'completed')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)
    if not _column_exists(conn, "tasks", "category_id"):
        conn.execute("ALTER TABLE tasks ADD COLUMN category_id INTEGER")
    if not _column_exists(conn, "tasks", "color"):
        conn.execute("ALTER TABLE tasks ADD COLUMN color TEXT DEFAULT ''")
    if not _column_exists(conn, "tasks", "task_type"):
        conn.execute("ALTER TABLE tasks ADD COLUMN task_type TEXT DEFAULT 'task'")
    if not _column_exists(conn, "tasks", "pos_x"):
        conn.execute("ALTER TABLE tasks ADD COLUMN pos_x INTEGER DEFAULT 0")
    if not _column_exists(conn, "tasks", "pos_y"):
        conn.execute("ALTER TABLE tasks ADD COLUMN pos_y INTEGER DEFAULT 0")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS board_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            color TEXT DEFAULT '',
            position INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def add_task(
    title,
    description="",
    due_date=None,
    is_starred=False,
    category_id=None,
    color="",
    task_type="task",
    pos_x=0,
    pos_y=0,
):
    """Add a new task to the database."""
    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO tasks (title, description, due_date, is_starred, category_id, color, task_type, pos_x, pos_y)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title,
            description,
            due_date,
            int(is_starred),
            category_id,
            color or "",
            task_type or "task",
            int(pos_x or 0),
            int(pos_y or 0),
        )
    )
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id


def get_active_tasks(include_quick: bool = False):
    """Get all active tasks sorted by the specified hierarchy."""
    conn = get_connection()
    where_quick = "" if include_quick else "AND COALESCE(task_type, 'task') != 'quick'"
    rows = conn.execute(
        f"""
        SELECT * FROM tasks WHERE status = 'active' {where_quick}
        ORDER BY
            is_starred DESC,
            CASE WHEN due_date IS NULL THEN 1 ELSE 0 END,
            due_date ASC
    """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_quick_tasks():
    """Get all active quick tasks for the sticky-note page."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT * FROM tasks
        WHERE status = 'active' AND COALESCE(task_type, 'task') = 'quick'
        ORDER BY created_at ASC
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_completed_tasks():
    """Get all completed tasks ordered by completion time descending."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM tasks WHERE status = 'completed'
        ORDER BY completed_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_tasks():
    """Get all tasks."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def complete_task(task_id):
    """Mark a task as completed."""
    conn = get_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE tasks SET status = 'completed', completed_at = ? WHERE id = ?",
        (now, task_id)
    )
    conn.commit()
    conn.close()


def delete_task(task_id):
    """Permanently delete a task."""
    conn = get_connection()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def toggle_star(task_id):
    """Toggle the starred status of a task."""
    conn = get_connection()
    conn.execute(
        "UPDATE tasks SET is_starred = CASE WHEN is_starred = 1 THEN 0 ELSE 1 END WHERE id = ?",
        (task_id,)
    )
    conn.commit()
    conn.close()


def set_task_star(task_id: int, is_starred: bool):
    """Set starred status directly."""
    conn = get_connection()
    conn.execute(
        "UPDATE tasks SET is_starred=? WHERE id=?",
        (1 if is_starred else 0, task_id)
    )
    conn.commit()
    conn.close()


def update_task(
    task_id,
    title,
    description="",
    due_date=None,
    is_starred=False,
    category_id=None,
    color="",
    task_type="task",
):
    """Update task details."""
    conn = get_connection()
    conn.execute(
        """
        UPDATE tasks
        SET title=?, description=?, due_date=?, is_starred=?, category_id=?, color=?, task_type=?
        WHERE id=?
        """,
        (
            title,
            description,
            due_date,
            int(is_starred),
            category_id,
            color or "",
            task_type or "task",
            task_id,
        )
    )
    conn.commit()
    conn.close()


def get_task_by_id(task_id):
    """Get a single task by its ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_tasks_for_month(year, month):
    """Get tasks that have a due_date or completed_at in a given month."""
    conn = get_connection()
    start = f"{year:04d}-{month:02d}-01"
    if month == 12:
        end = f"{year + 1:04d}-01-01"
    else:
        end = f"{year:04d}-{month + 1:02d}-01"
    rows = conn.execute("""
        SELECT * FROM tasks
        WHERE (due_date >= ? AND due_date < ?)
           OR (completed_at >= ? AND completed_at < ?)
        ORDER BY due_date ASC, completed_at ASC
    """, (start, end, start, end)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_board_categories():
    """Get all Kanban categories in display order."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM board_categories ORDER BY position ASC, id ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_board_category(name: str, color: str = "") -> int:
    """Create a Kanban category."""
    conn = get_connection()
    row = conn.execute("SELECT COALESCE(MAX(position), -1) + 1 FROM board_categories").fetchone()
    position = row[0] if row else 0
    cursor = conn.execute(
        "INSERT INTO board_categories (name, color, position) VALUES (?, ?, ?)",
        (name.strip(), color or "", position)
    )
    cat_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return cat_id


def update_board_category(category_id: int, name: str, color: str = ""):
    """Update category metadata."""
    conn = get_connection()
    conn.execute(
        "UPDATE board_categories SET name=?, color=? WHERE id=?",
        (name.strip(), color or "", category_id)
    )
    conn.commit()
    conn.close()


def delete_board_category(category_id: int):
    """Delete a category and move its tasks back to uncategorized."""
    conn = get_connection()
    conn.execute("UPDATE tasks SET category_id=NULL WHERE category_id=?", (category_id,))
    conn.execute("DELETE FROM board_categories WHERE id=?", (category_id,))
    conn.commit()
    conn.close()


def update_board_category_positions(category_ids: list[int]):
    """Persist category display order by id sequence."""
    conn = get_connection()
    for idx, cat_id in enumerate(category_ids):
        conn.execute(
            "UPDATE board_categories SET position=? WHERE id=?",
            (idx, cat_id)
        )
    conn.commit()
    conn.close()


def update_task_category(task_id: int, category_id: Optional[int]):
    """Move a task to another Kanban category."""
    conn = get_connection()
    conn.execute("UPDATE tasks SET category_id=? WHERE id=?", (category_id, task_id))
    conn.commit()
    conn.close()


def update_task_color(task_id: int, color: str = ""):
    """Update a task card color."""
    conn = get_connection()
    conn.execute("UPDATE tasks SET color=? WHERE id=?", (color or "", task_id))
    conn.commit()
    conn.close()


def update_task_position(task_id: int, pos_x: int, pos_y: int):
    """Update saved card position for sticky quick tasks."""
    conn = get_connection()
    conn.execute(
        "UPDATE tasks SET pos_x=?, pos_y=? WHERE id=?",
        (int(pos_x), int(pos_y), task_id),
    )
    conn.commit()
    conn.close()


# ── Notes CRUD ──────────────────────────────────────────────

def add_note(content: str) -> int:
    """Add a new note. Returns the note id."""
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO notes (content) VALUES (?)", (content,)
    )
    note_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return note_id


def get_all_notes() -> list[dict]:
    """Get all notes ordered by most-recently updated first."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM notes ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_note(note_id: int, content: str):
    """Update a note's content."""
    conn = get_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE notes SET content=?, updated_at=? WHERE id=?",
        (content, now, note_id)
    )
    conn.commit()
    conn.close()


def delete_note(note_id: int):
    """Permanently delete a note."""
    conn = get_connection()
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
