"""Date parsing utilities for the Todo List application."""

from datetime import datetime, date


def parse_due_date(text: str) -> str | None:
    """
    Parse a due date string according to the SRS:
    - Format A (MM/DD): Auto-infer year. If MM/DD < today → next year.
    - Format B (YYYY/MM/DD): Explicit date.
    - Format C (Empty): Return None.
    Returns ISO format string (YYYY-MM-DD) or None.
    """
    if not text or not text.strip():
        return None

    text = text.strip().replace("-", "/")
    parts = text.split("/")

    today = date.today()

    try:
        if len(parts) == 2:
            month = int(parts[0])
            day = int(parts[1])
            candidate = date(today.year, month, day)
            if candidate < today:
                candidate = date(today.year + 1, month, day)
            return candidate.isoformat()

        elif len(parts) == 3:
            year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2])
            return date(year, month, day).isoformat()

    except (ValueError, IndexError):
        return None

    return None


def format_due_date(iso_date: str | None) -> str:
    """Format an ISO date string for display."""
    if not iso_date:
        return "No due date"
    try:
        d = date.fromisoformat(iso_date[:10])
        return d.strftime("%Y/%m/%d")
    except (ValueError, TypeError):
        return "No due date"


def format_datetime(dt_str: str | None) -> str:
    """Format a datetime string for display."""
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y/%m/%d %H:%M")
    except (ValueError, TypeError):
        return ""


def is_overdue(iso_date: str | None) -> bool:
    """Check if a due date is before today."""
    if not iso_date:
        return False
    try:
        d = date.fromisoformat(iso_date[:10])
        return d < date.today()
    except (ValueError, TypeError):
        return False


def days_until(iso_date: str | None) -> int | None:
    """Return number of days until due date. Negative if overdue."""
    if not iso_date:
        return None
    try:
        d = date.fromisoformat(iso_date[:10])
        return (d - date.today()).days
    except (ValueError, TypeError):
        return None
