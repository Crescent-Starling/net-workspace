from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.common import ApiResponse, PaginationMeta
from app.schemas.template import (
    TemplateCreate,
    TemplateDetailResponse,
    TemplateResponse,
    TemplateUpdate,
    TemplateVersionResponse,
)
from app.services.template_service import (
    create_template,
    get_template_detail,
    list_templates,
    update_template,
)

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])


@router.get("/", response_model=ApiResponse[list[TemplateResponse]])
async def list_templates_api(
    workspace_id: int | None = Query(None),
    template_scope: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List templates with optional filters."""
    templates, total = await list_templates(
        db,
        workspace_id=workspace_id,
        template_scope=template_scope,
        status=status_filter,
        page=page,
        page_size=page_size,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return ApiResponse(
        data=[TemplateResponse.model_validate(t) for t in templates],
        meta=PaginationMeta(total=total, page=page, page_size=page_size, total_pages=total_pages),
    )


@router.post("/", response_model=ApiResponse[TemplateResponse])
async def create_template_api(
    data: TemplateCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Create a new template with initial DSL version."""
    from app.services.workspace_service import list_workspaces

    workspaces = await list_workspaces(db, current_user.id)
    if not workspaces:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No workspace found. Create a workspace first.",
        )

    template = await create_template(db, workspaces[0].id, current_user.id, data)
    return ApiResponse(data=TemplateResponse.model_validate(template))


@router.get("/{template_id}", response_model=ApiResponse[TemplateDetailResponse])
async def get_template_api(
    template_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get template detail with current version DSL."""
    template = await get_template_detail(db, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    current_version = None
    if template.current_version:
        current_version = TemplateVersionResponse.model_validate(template.current_version)

    return ApiResponse(
        data=TemplateDetailResponse(
            **TemplateResponse.model_validate(template).model_dump(),
            current_version=current_version,
        )
    )


@router.put("/{template_id}", response_model=ApiResponse[TemplateResponse])
async def update_template_api(
    template_id: int,
    data: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update template metadata."""
    template = await get_template_detail(db, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    updated = await update_template(db, template, data.display_name, data.status)
    return ApiResponse(data=TemplateResponse.model_validate(updated))
