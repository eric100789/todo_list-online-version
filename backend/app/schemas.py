from pydantic import BaseModel, EmailStr
from typing import Optional, Any
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    identity: Optional[str] = None
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: str
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True


class TokenOut(BaseModel):
    token: str


class SessionOut(BaseModel):
    id: int
    token: str
    device_info: Optional[str] = None
    created_at: datetime
    is_current: bool = False


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None


class TaskOut(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    due_date: Optional[str] = None
    is_starred: bool = False
    status: str = "active"
    completed: bool
    created_at: datetime
    completed_at: Optional[datetime] = None
    auto_completed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    category_id: Optional[Any] = None
    color: str = ""
    task_type: str = "task"
    pos_x: int = 0
    pos_y: int = 0

    class Config:
        orm_mode = True
