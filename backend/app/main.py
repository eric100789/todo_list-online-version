from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, status, Body, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from .database import get_db, engine, Base
from . import models, schemas, auth
from .config import settings


app = FastAPI(title="Todo - API")


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS due_date VARCHAR(32)"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS is_starred BOOLEAN DEFAULT FALSE"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS status VARCHAR(32) DEFAULT 'active'"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP NULL"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS auto_completed_at TIMESTAMP NULL"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS category_id INTEGER NULL"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS color VARCHAR(64) DEFAULT ''"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS task_type VARCHAR(32) DEFAULT 'task'"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS pos_x INTEGER DEFAULT 0"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS pos_y INTEGER DEFAULT 0"))
        await conn.execute(text("CREATE TABLE IF NOT EXISTS board_categories (id SERIAL PRIMARY KEY, user_id INTEGER NULL, name VARCHAR(255) NOT NULL, color VARCHAR(64) DEFAULT '', position INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT NOW())"))
        await conn.execute(text("CREATE TABLE IF NOT EXISTS notes (id SERIAL PRIMARY KEY, user_id INTEGER NULL, content TEXT NOT NULL DEFAULT '', created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW())"))


def _task_dict(task: models.Task) -> dict:
    return {
        "id": task.id,
        "user_id": task.user_id,
        "title": task.title,
        "description": task.description or "",
        "due_date": task.due_date,
        "is_starred": bool(task.is_starred),
        "status": task.status or ("completed" if task.completed else "active"),
        "completed": bool(task.completed),
        "created_at": task.created_at,
        "completed_at": task.completed_at,
        "auto_completed_at": task.auto_completed_at,
        "updated_at": task.updated_at,
        "category_id": task.category_id,
        "color": task.color or "",
        "task_type": task.task_type or "task",
        "pos_x": task.pos_x or 0,
        "pos_y": task.pos_y or 0,
    }


def _session_dict(session: models.Session, current_token: str | None = None) -> dict:
    return {
        "id": session.id,
        "token": session.token,
        "device_info": session.device_info,
        "created_at": session.created_at,
        "is_current": bool(current_token and session.token == current_token),
    }


@app.post("/auth/register", response_model=schemas.UserOut)
async def register(payload: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    if not settings.ENABLE_REGISTRATION:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Registration disabled")
    q = select(models.User).where((models.User.email == payload.email) | (models.User.username == payload.username))
    res = await db.execute(q)
    if res.scalars().first():
        raise HTTPException(status_code=400, detail="Email or username already in use")
    user = models.User(email=payload.email, username=payload.username, password_hash=auth.hash_password(payload.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@app.post("/auth/login", response_model=schemas.TokenOut)
async def login(payload: schemas.UserLogin, db: AsyncSession = Depends(get_db)):
    identity = (payload.identity or payload.email or payload.username or "").strip()
    if not identity:
        raise HTTPException(status_code=400, detail="Email or username is required")
    q = select(models.User).where((models.User.email == identity) | (models.User.username == identity))
    res = await db.execute(q)
    user = res.scalars().first()
    if not user or not auth.verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = await auth.create_session(db, user)
    return {"token": token}


@app.post("/auth/logout")
async def logout(current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db), authorization: str | None = Header(None)):
    if not authorization:
        raise HTTPException(status_code=400, detail="No authorization header")
    token = authorization.split(" ", 1)[1]
    await db.execute(select(models.Session).where(models.Session.token == token))
    await db.execute(models.Session.__table__.delete().where(models.Session.token == token))
    await db.commit()
    return {"ok": True}


@app.post("/auth/revoke_others")
async def revoke_others(current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db), authorization: str | None = Header(None)):
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
    await db.execute(models.Session.__table__.delete().where((models.Session.user_id == current_user.id) & (models.Session.token != token)))
    await db.commit()
    return {"ok": True}


@app.get("/auth/sessions", response_model=list[schemas.SessionOut])
async def list_sessions(current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db), authorization: str | None = Header(None)):
    current_token = None
    if authorization and authorization.startswith("Bearer "):
        current_token = authorization.split(" ", 1)[1]
    q = select(models.Session).where(models.Session.user_id == current_user.id).order_by(models.Session.created_at.desc(), models.Session.id.desc())
    res = await db.execute(q)
    return [_session_dict(session, current_token=current_token) for session in res.scalars().all()]


@app.post("/auth/sessions/revoke")
async def revoke_sessions(payload: dict = Body(...), current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db), authorization: str | None = Header(None)):
    raw_ids = payload.get("session_ids", [])
    session_ids = []
    for value in raw_ids:
        try:
            session_ids.append(int(value))
        except (TypeError, ValueError):
            continue
    if not session_ids:
        raise HTTPException(status_code=400, detail="No session ids provided")

    current_token = None
    if authorization and authorization.startswith("Bearer "):
        current_token = authorization.split(" ", 1)[1]

    q = select(models.Session).where((models.Session.user_id == current_user.id) & (models.Session.id.in_(session_ids)))
    res = await db.execute(q)
    sessions = res.scalars().all()
    revoked_current = any(session.token == current_token for session in sessions)
    revoked_ids = [session.id for session in sessions]
    for session in sessions:
        await db.delete(session)
    await db.commit()
    return {"ok": True, "revoked_current": revoked_current, "revoked_ids": revoked_ids}


@app.get("/users/me", response_model=schemas.UserOut)
async def me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@app.post("/tasks", response_model=schemas.TaskOut)
async def create_task(payload: schemas.TaskCreate, current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    task = models.Task(user_id=current_user.id, title=payload.title, description=payload.description, status="active", completed=False, is_starred=False)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return _task_dict(task)


@app.get("/tasks")
async def list_tasks(current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(models.Task).where(models.Task.user_id == current_user.id)
    res = await db.execute(q)
    return [_task_dict(task) for task in res.scalars().all()]


@app.patch("/tasks/{task_id}")
async def update_task(task_id: int, payload: dict = Body(...), current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(models.Task).where((models.Task.id == task_id) & (models.Task.user_id == current_user.id))
    res = await db.execute(q)
    task = res.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if "title" in payload:
        task.title = payload["title"]
    if "description" in payload:
        task.description = payload["description"]
    if "due_date" in payload:
        task.due_date = payload["due_date"]
    if "is_starred" in payload:
        task.is_starred = bool(payload["is_starred"])
    if "status" in payload:
        task.status = payload["status"]
        task.completed = payload["status"] == "completed"
        task.completed_at = datetime.utcnow() if task.completed else None
    if payload.get("auto_completed"):
        task.status = "completed"
        task.completed = True
        task.completed_at = task.completed_at or datetime.utcnow()
        task.auto_completed_at = task.auto_completed_at or datetime.utcnow()
    if "completed" in payload:
        task.completed = bool(payload["completed"])
        task.status = "completed" if task.completed else "active"
        task.completed_at = datetime.utcnow() if task.completed else None
        if task.completed and payload.get("auto_completed"):
            task.auto_completed_at = datetime.utcnow()
    if "category_id" in payload:
        task.category_id = payload["category_id"]
    if "color" in payload:
        task.color = payload["color"] or ""
    if "task_type" in payload:
        task.task_type = payload["task_type"] or "task"
    if "pos_x" in payload:
        task.pos_x = int(payload["pos_x"] or 0)
    if "pos_y" in payload:
        task.pos_y = int(payload["pos_y"] or 0)
    task.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(task)
    return _task_dict(task)


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(models.Task).where((models.Task.id == task_id) & (models.Task.user_id == current_user.id))
    res = await db.execute(q)
    task = res.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task)
    await db.commit()
    return {"ok": True}


@app.get("/categories")
async def list_categories(current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(models.Category).order_by(models.Category.position.asc(), models.Category.id.asc())
    res = await db.execute(q)
    return [{"id": cat.id, "name": cat.name, "color": cat.color or "", "position": cat.position, "created_at": cat.created_at} for cat in res.scalars().all()]


@app.post("/categories")
async def create_category(payload: dict = Body(...), current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(models.Category).order_by(models.Category.position.desc(), models.Category.id.desc())
    res = await db.execute(q)
    last = res.scalars().first()
    position = (last.position + 1) if last else 0
    category = models.Category(user_id=current_user.id, name=payload.get("name", "").strip(), color=payload.get("color", "") or "", position=position)
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return {"id": category.id, "name": category.name, "color": category.color, "position": category.position, "created_at": category.created_at}


@app.patch("/categories/{category_id}")
async def update_category(category_id: int, payload: dict = Body(...), current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(models.Category).where(models.Category.id == category_id)
    res = await db.execute(q)
    category = res.scalars().first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if "name" in payload:
        category.name = payload["name"].strip()
    if "color" in payload:
        category.color = payload["color"] or ""
    await db.commit()
    await db.refresh(category)
    return {"id": category.id, "name": category.name, "color": category.color, "position": category.position, "created_at": category.created_at}


@app.delete("/categories/{category_id}")
async def delete_category(category_id: int, current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(models.Category).where(models.Category.id == category_id)
    res = await db.execute(q)
    category = res.scalars().first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    await db.execute(text("UPDATE tasks SET category_id = NULL WHERE category_id = :category_id"), {"category_id": category_id})
    await db.delete(category)
    await db.commit()
    return {"ok": True}


@app.post("/categories/reorder")
async def reorder_categories(payload: dict = Body(...), current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    for idx, category_id in enumerate(payload.get("category_ids", [])):
        await db.execute(text("UPDATE board_categories SET position = :pos WHERE id = :id"), {"pos": idx, "id": category_id})
    await db.commit()
    return {"ok": True}


@app.get("/notes")
async def list_notes(current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(models.Note).order_by(models.Note.updated_at.desc(), models.Note.id.desc())
    res = await db.execute(q)
    return [{"id": note.id, "content": note.content, "created_at": note.created_at, "updated_at": note.updated_at} for note in res.scalars().all()]


@app.post("/notes")
async def create_note(payload: dict = Body(...), current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    note = models.Note(user_id=current_user.id, content=payload.get("content", ""))
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return {"id": note.id, "content": note.content, "created_at": note.created_at, "updated_at": note.updated_at}


@app.patch("/notes/{note_id}")
async def update_note(note_id: int, payload: dict = Body(...), current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(models.Note).where(models.Note.id == note_id)
    res = await db.execute(q)
    note = res.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if "content" in payload:
        note.content = payload["content"]
    note.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(note)
    return {"id": note.id, "content": note.content, "created_at": note.created_at, "updated_at": note.updated_at}


@app.delete("/notes/{note_id}")
async def delete_note(note_id: int, current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(models.Note).where(models.Note.id == note_id)
    res = await db.execute(q)
    note = res.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    await db.delete(note)
    await db.commit()
    return {"ok": True}