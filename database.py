"""HTTP API adapter for the Todo List PyQt6 application.

The original SQLite implementation has been moved to `database_sqlite.py`.
This module preserves the same public function names, but routes operations
through the FastAPI backend via httpx.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from typing import Optional, Any

import httpx


def _get_data_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


DATA_DIR = _get_data_dir()
API_BASE_URL = os.environ.get("TODO_API_BASE_URL", "http://127.0.0.1:8000")
TOKEN_PATH = os.path.join(DATA_DIR, "api_token.json")


def _token_from_file() -> str | None:
    try:
        with open(TOKEN_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("token") or None
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _save_token(token: str | None) -> None:
    if not token:
        try:
            os.remove(TOKEN_PATH)
        except FileNotFoundError:
            pass
        return
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        json.dump({"token": token}, f)


def set_api_token(token: str | None) -> None:
    _save_token(token)


def get_api_token() -> str | None:
    return _token_from_file()


def _headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    token = get_api_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _request(method: str, path: str, *, json_body: Any = None, params: dict[str, Any] | None = None):
    url = f"{API_BASE_URL.rstrip('/')}{path}"
    with httpx.Client(timeout=20.0) as client:
        response = client.request(method, url, headers=_headers(), json=json_body, params=params)
    response.raise_for_status()
    if response.headers.get("content-type", "").startswith("application/json"):
        return response.json()
    return response.text


def _coerce_task(task: dict) -> dict:
    return {
        "id": task.get("id"),
        "title": task.get("title", ""),
        "description": task.get("description", ""),
        "due_date": task.get("due_date"),
        "is_starred": bool(task.get("is_starred", False)),
        "status": task.get("status", "active"),
        "created_at": task.get("created_at"),
        "completed_at": task.get("completed_at"),
        "category_id": task.get("category_id"),
        "color": task.get("color", ""),
        "task_type": task.get("task_type", "task"),
        "pos_x": task.get("pos_x", 0),
        "pos_y": task.get("pos_y", 0),
    }


def init_db():
    """Compatibility shim for the old startup call.

    The backend now owns persistence. This function just validates the API is
    reachable when the desktop app starts.
    """
    try:
        _request("GET", "/docs")
    except Exception:
        # Avoid blocking the GUI on startup if the API is not ready yet.
        pass


def login(email_or_username: str, password: str) -> str:
    payload = {"email": email_or_username, "username": email_or_username, "password": password}
    data = _request("POST", "/auth/login", json_body=payload)
    token = data["token"]
    set_api_token(token)
    return token


def register(email: str, username: str, password: str) -> dict:
    payload = {"email": email, "username": username, "password": password}
    data = _request("POST", "/auth/register", json_body=payload)
    return data


def logout():
    try:
        _request("POST", "/auth/logout")
    finally:
        set_api_token(None)


def revoke_other_sessions():
    _request("POST", "/auth/revoke_others")


def get_current_user() -> dict:
    return _request("GET", "/users/me")


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
    payload = {
        "title": title,
        "description": description,
        "due_date": due_date,
        "is_starred": is_starred,
        "category_id": category_id,
        "color": color,
        "task_type": task_type,
        "pos_x": pos_x,
        "pos_y": pos_y,
    }
    data = _request("POST", "/tasks", json_body=payload)
    return data["id"]


def get_active_tasks(include_quick: bool = False):
    tasks = _request("GET", "/tasks")
    filtered = [
        _coerce_task(task)
        for task in tasks
        if task.get("status", "active") == "active"
        and (include_quick or task.get("task_type", "task") != "quick")
    ]
    filtered.sort(key=lambda task: (
        not bool(task.get("is_starred", False)),
        task.get("due_date") is None,
        task.get("due_date") or "",
    ))
    return filtered


def get_quick_tasks():
    return [task for task in get_active_tasks(include_quick=True) if task.get("task_type", "task") == "quick"]


def get_completed_tasks():
    return [task for task in _request("GET", "/tasks") if task.get("status") == "completed"]


def get_all_tasks():
    return [_coerce_task(task) for task in _request("GET", "/tasks")]


def complete_task(task_id):
    _request("PATCH", f"/tasks/{task_id}", json_body={"completed": True, "status": "completed"})


def delete_task(task_id):
    _request("DELETE", f"/tasks/{task_id}")


def toggle_star(task_id):
    task = get_task_by_id(task_id)
    if task:
        _request("PATCH", f"/tasks/{task_id}", json_body={"is_starred": not bool(task.get("is_starred"))})


def set_task_star(task_id: int, is_starred: bool):
    _request("PATCH", f"/tasks/{task_id}", json_body={"is_starred": bool(is_starred)})


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
    payload = {
        "title": title,
        "description": description,
        "due_date": due_date,
        "is_starred": is_starred,
        "category_id": category_id,
        "color": color,
        "task_type": task_type,
    }
    _request("PATCH", f"/tasks/{task_id}", json_body=payload)


def get_task_by_id(task_id):
    tasks = _request("GET", "/tasks")
    for task in tasks:
        if task.get("id") == task_id:
            return _coerce_task(task)
    return None


def get_tasks_for_month(year, month):
    # The current backend does not expose month filtering; use client-side filter.
    start = f"{year:04d}-{month:02d}-01"
    if month == 12:
        end = f"{year + 1:04d}-01-01"
    else:
        end = f"{year:04d}-{month + 1:02d}-01"
    result = []
    for task in _request("GET", "/tasks"):
        due_date = task.get("due_date")
        completed_at = task.get("completed_at")
        if (due_date and start <= due_date < end) or (completed_at and start <= completed_at < end):
            result.append(_coerce_task(task))
    return result


def get_board_categories():
    return _request("GET", "/categories")


def add_board_category(name: str, color: str = "") -> int:
    data = _request("POST", "/categories", json_body={"name": name, "color": color})
    return data["id"]


def update_board_category(category_id: int, name: str, color: str = ""):
    _request("PATCH", f"/categories/{category_id}", json_body={"name": name, "color": color})


def delete_board_category(category_id: int):
    _request("DELETE", f"/categories/{category_id}")


def update_board_category_positions(category_ids: list[int]):
    _request("POST", "/categories/reorder", json_body={"category_ids": category_ids})


def update_task_category(task_id: int, category_id: Optional[int]):
    _request("PATCH", f"/tasks/{task_id}", json_body={"category_id": category_id})


def update_task_color(task_id: int, color: str = ""):
    _request("PATCH", f"/tasks/{task_id}", json_body={"color": color})


def update_task_position(task_id: int, pos_x: int, pos_y: int):
    _request("PATCH", f"/tasks/{task_id}", json_body={"pos_x": pos_x, "pos_y": pos_y})


def add_note(content: str) -> int:
    data = _request("POST", "/notes", json_body={"content": content})
    return data["id"]


def get_all_notes() -> list[dict]:
    return _request("GET", "/notes")


def update_note(note_id: int, content: str):
    _request("PATCH", f"/notes/{note_id}", json_body={"content": content})


def delete_note(note_id: int):
    _request("DELETE", f"/notes/{note_id}")
