"""Tasks API – 任务 CRUD + 触发执行。"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.task import CrawlTask, TaskRunLog
from app.models.user import User
from app.schemas.common import ApiResponse, PaginationMeta
from app.schemas.task import TaskCreate, TaskDetailResponse, TaskResponse, TaskRunLogResponse, TaskUpdate
from app.services.task_service import create_task, get_task, list_tasks, update_task_status
from app.services.task_executor import execute_task

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.get("/", response_model=ApiResponse[list[TaskResponse]])
async def list_tasks_api(
    workspace_id: int = Query(..., description="Filter by workspace ID"),
    task_status: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List crawl tasks for a workspace."""
    tasks, total = await list_tasks(db, workspace_id, task_status, page, page_size)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return ApiResponse(
        data=[TaskResponse.model_validate(t) for t in tasks],
        meta=PaginationMeta(total=total, page=page, page_size=page_size, total_pages=total_pages),
    )


@router.post("/", response_model=ApiResponse[TaskResponse])
async def create_task_api(
    data: TaskCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Create a new crawl task."""
    from app.services.workspace_service import list_workspaces

    workspaces = await list_workspaces(db, current_user.id)
    ws_id = workspaces[0].id if workspaces else 1
    task = await create_task(db, ws_id, current_user.id, data)
    return ApiResponse(data=TaskResponse.model_validate(task))


@router.get("/{task_id}", response_model=ApiResponse[TaskDetailResponse])
async def get_task_api(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get task detail with run logs."""
    task = await get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    result = await db.execute(
        select(TaskRunLog).where(TaskRunLog.task_id == task_id).order_by(TaskRunLog.created_at)
    )
    logs = result.scalars().all()

    return ApiResponse(
        data=TaskDetailResponse(
            **TaskResponse.model_validate(task).model_dump(),
            logs=[TaskRunLogResponse.model_validate(log) for log in logs],
        ),
    )


@router.put("/{task_id}", response_model=ApiResponse[TaskResponse])
async def update_task_api(
    task_id: int,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update task status."""
    task = await get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if data.task_status is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided")
    updated = await update_task_status(db, task, data.task_status)
    return ApiResponse(data=TaskResponse.model_validate(updated))


@router.post("/{task_id}/execute", response_model=ApiResponse[dict[str, Any]])
async def execute_task_api(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Trigger task execution synchronously (V1 简化，后续可改为后台）。"""
    result = await execute_task(db, task_id, current_user.id)
    if not result.get("ok"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "执行失败"),
        )
    return ApiResponse(data=result)
