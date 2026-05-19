from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from passlib.context import CryptContext
from uuid import uuid4
from .database import get_db
from . import models
from .config import settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


async def create_session(db: AsyncSession, user: models.User, device_info: str | None = None) -> str:
    # Remove existing sessions to enforce single-device session
    await db.execute(delete(models.Session).where(models.Session.user_id == user.id))
    token = uuid4().hex
    session = models.Session(user_id=user.id, token=token, device_info=device_info)
    db.add(session)
    await db.commit()
    return token


async def get_current_user(authorization: str | None = Header(None), db: AsyncSession = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")
    token = authorization.split(" ", 1)[1]
    q = select(models.Session).where(models.Session.token == token)
    res = await db.execute(q)
    session = res.scalars().first()
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or revoked token")
    q2 = select(models.User).where(models.User.id == session.user_id)
    res2 = await db.execute(q2)
    user = res2.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
