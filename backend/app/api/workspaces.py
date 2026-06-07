from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate
from app.services.workspace_service import (
    create_workspace,
    get_workspace,
    list_workspaces,
    update_workspace,
)

router = APIRouter(prefix="/api/v1/workspaces", tags=["workspaces"])


@router.get("/", response_model=ApiResponse[list[WorkspaceResponse]])
async def list_user_workspaces(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """List all workspaces for the current user."""
    workspaces = await list_workspaces(db, current_user.id)
    return ApiResponse(data=[WorkspaceResponse.model_validate(ws) for ws in workspaces])


@router.post("/", response_model=ApiResponse[WorkspaceResponse])
async def create_user_workspace(
    data: WorkspaceCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Create a new workspace."""
    ws = await create_workspace(db, current_user.id, data)
    return ApiResponse(data=WorkspaceResponse.model_validate(ws))


@router.get("/{workspace_id}", response_model=ApiResponse[WorkspaceResponse])
async def get_user_workspace(
    workspace_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Get workspace by ID."""
    ws = await get_workspace(db, workspace_id, current_user.id)
    if ws is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return ApiResponse(data=WorkspaceResponse.model_validate(ws))


@router.put("/{workspace_id}", response_model=ApiResponse[WorkspaceResponse])
async def update_user_workspace(
    workspace_id: int,
    data: WorkspaceUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Update workspace."""
    ws = await get_workspace(db, workspace_id, current_user.id)
    if ws is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    updated = await update_workspace(db, ws, data)
    return ApiResponse(data=WorkspaceResponse.model_validate(updated))
