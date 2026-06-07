from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import CrawlTask

if TYPE_CHECKING:
    from app.schemas.task import TaskCreate


async def create_task(
    db: AsyncSession, workspace_id: int, user_id: int, data: TaskCreate
) -> CrawlTask:
    """Create a new crawl task."""
    task = CrawlTask(
        workspace_id=workspace_id,
        template_version_id=data.template_version_id,
        created_by_user_id=user_id,
        task_name=data.task_name,
        task_status="draft",
        task_params=data.task_params,
        schedule_type=data.schedule_type,
        scheduled_at=data.scheduled_at,
    )
    db.add(task)
    await db.flush()
    return task


async def list_tasks(
    db: AsyncSession,
    workspace_id: int,
    task_status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[CrawlTask], int]:
    """List tasks for a workspace."""
    query = select(CrawlTask).where(CrawlTask.workspace_id == workspace_id)
    count_query = select(func.count()).select_from(CrawlTask).where(
        CrawlTask.workspace_id == workspace_id
    )

    if task_status is not None:
        query = query.where(CrawlTask.task_status == task_status)
        count_query = count_query.where(CrawlTask.task_status == task_status)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(
        query.order_by(CrawlTask.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.scalars().all()), total


async def get_task(db: AsyncSession, task_id: int) -> CrawlTask | None:
    """Get task by ID."""
    result = await db.execute(select(CrawlTask).where(CrawlTask.id == task_id))
    return result.scalar_one_or_none()


async def update_task_status(
    db: AsyncSession, task: CrawlTask, task_status: str
) -> CrawlTask:
    """Update task status."""
    task.task_status = task_status
    await db.flush()
    return task
