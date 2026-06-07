from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.source import Source
from app.schemas.common import ApiResponse
from app.schemas.source import SourceCreate, SourceResponse

router = APIRouter(prefix="/api/v1/sources", tags=["sources"])


@router.get("/", response_model=ApiResponse[list[SourceResponse]])
async def list_sources(db: AsyncSession = Depends(get_db)):
    """List all data sources."""
    result = await db.execute(
        select(Source).where(Source.status == "active").order_by(Source.source_name)
    )
    sources = result.scalars().all()
    return ApiResponse(data=[SourceResponse.model_validate(s) for s in sources])


@router.post("/", response_model=ApiResponse[SourceResponse])
async def create_source(
    data: SourceCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new data source."""
    source = Source(
        source_name=data.source_name,
        domain=data.domain,
        source_type=data.source_type,
        content_type=data.content_type,
        site_locale=data.site_locale,
        status="active",
    )
    db.add(source)
    await db.flush()
    return ApiResponse(data=SourceResponse.model_validate(source))
