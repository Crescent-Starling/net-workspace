from __future__ import annotations

import re
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Workspace

if TYPE_CHECKING:
    from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate


def _generate_slug(name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", name.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    return slug


async def create_workspace(
    db: AsyncSession, user_id: int, data: WorkspaceCreate
) -> Workspace:
    """Create a workspace for the user. Auto-generates slug from name."""
    slug = _generate_slug(data.name)
    # Ensure slug uniqueness within user scope
    existing = await db.execute(
        select(Workspace).where(Workspace.user_id == user_id, Workspace.slug == slug)
    )
    if existing.scalar_one_or_none():
        slug = f"{slug}-{1}"  # simple dedup

    ws = Workspace(
        user_id=user_id,
        name=data.name,
        slug=slug,
        description=data.description,
        status="active",
    )
    db.add(ws)
    await db.flush()
    return ws


async def list_workspaces(
    db: AsyncSession, user_id: int
) -> list[Workspace]:
    """List all workspaces for a user."""
    result = await db.execute(
        select(Workspace)
        .where(Workspace.user_id == user_id, Workspace.status == "active")
        .order_by(Workspace.created_at.desc())
    )
    return list(result.scalars().all())


async def get_workspace(
    db: AsyncSession, workspace_id: int, user_id: int
) -> Workspace | None:
    """Get workspace by ID, scoped to user."""
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def update_workspace(
    db: AsyncSession, workspace: Workspace, data: WorkspaceUpdate
) -> Workspace:
    """Update workspace fields."""
    if data.name is not None:
        workspace.name = data.name
        workspace.slug = _generate_slug(data.name)
    if data.description is not None:
        workspace.description = data.description
    await db.flush()
    return workspace
