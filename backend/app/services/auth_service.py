from __future__ import annotations

import re
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import hash_password, verify_password
from app.models.user import User

if TYPE_CHECKING:
    from app.schemas.auth import UserRegister


def _generate_slug(name: str) -> str:
    """Convert name to URL-safe slug."""
    slug = re.sub(r"[^\w\s-]", "", name.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    return slug


async def register_user(db: AsyncSession, data: UserRegister) -> User:
    """Create a new user account."""
    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        role="user",
        status="active",
    )
    db.add(user)
    await db.flush()
    return user


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> User | None:
    """Verify username and password, return user if valid."""
    result = await db.execute(
        select(User).where(User.username == username, User.status == "active")
    )
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Get user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
