from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.template import Template, TemplateVersion

if TYPE_CHECKING:
    from app.schemas.template import TemplateCreate


async def create_template(
    db: AsyncSession, workspace_id: int, user_id: int, data: TemplateCreate
) -> Template:
    """Create a template with its first version."""
    template = Template(
        workspace_id=workspace_id,
        source_id=data.source_id,
        template_name=data.template_name,
        display_name=data.display_name,
        template_scope=data.template_scope,
        status="draft",
    )
    db.add(template)
    await db.flush()

    # Create first version
    version = TemplateVersion(
        template_id=template.id,
        version="v1",
        dsl_content=data.dsl_content,
        generation_source="manual",
        created_by_user_id=user_id,
    )
    db.add(version)
    await db.flush()

    template.current_version_id = version.id
    await db.flush()
    await db.refresh(template)
    return template


async def list_templates(
    db: AsyncSession,
    workspace_id: int | None = None,
    template_scope: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Template], int]:
    """List templates with optional filters."""
    query = select(Template)
    count_query = select(func.count()).select_from(Template)

    if workspace_id is not None:
        query = query.where(Template.workspace_id == workspace_id)
        count_query = count_query.where(Template.workspace_id == workspace_id)
    if template_scope is not None:
        query = query.where(Template.template_scope == template_scope)
        count_query = count_query.where(Template.template_scope == template_scope)
    if status is not None:
        query = query.where(Template.status == status)
        count_query = count_query.where(Template.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(
        query.order_by(Template.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    templates = list(result.scalars().all())
    return templates, total


async def get_template_detail(
    db: AsyncSession, template_id: int
) -> Template | None:
    """Get template with eager-loaded current version."""
    result = await db.execute(
        select(Template).where(Template.id == template_id)
    )
    return result.scalar_one_or_none()


async def update_template(
    db: AsyncSession, template: Template, display_name: str | None, status: str | None
) -> Template:
    """Update template display_name or status."""
    if display_name is not None:
        template.display_name = display_name
    if status is not None:
        template.status = status
    await db.flush()
    await db.refresh(template)
    return template


async def add_template_version(
    db: AsyncSession,
    template_id: int,
    dsl_content: dict,
    generation_source: str,
    user_id: int | None = None,
    confidence_level: str | None = None,
    change_summary: str | None = None,
) -> TemplateVersion:
    """Add a new version to a template."""
    # Get latest version number
    result = await db.execute(
        select(TemplateVersion)
        .where(TemplateVersion.template_id == template_id)
        .order_by(TemplateVersion.created_at.desc())
        .limit(1)
    )
    latest = result.scalar_one_or_none()
    if latest:
        num = int(latest.version.replace("v", "")) + 1
    else:
        num = 1
    new_version_str = f"v{num}"

    version = TemplateVersion(
        template_id=template_id,
        version=new_version_str,
        dsl_content=dsl_content,
        generation_source=generation_source,
        confidence_level=confidence_level,
        change_summary=change_summary,
        created_by_user_id=user_id,
    )
    db.add(version)
    await db.flush()

    # Update template's current version
    result = await db.execute(
        select(Template).where(Template.id == template_id)
    )
    template = result.scalar_one()
    template.current_version_id = version.id
    await db.flush()
    return version
