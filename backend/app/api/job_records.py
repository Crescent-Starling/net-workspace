from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.common import ApiResponse, PaginationMeta
from app.schemas.job_record import JobRecordFilter, JobRecordResponse, JobRecordStatsResponse
from app.services.search_service import get_job_record, get_job_stats, list_job_records

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("/", response_model=ApiResponse[list[JobRecordResponse]])
async def list_jobs_api(
    workspace_id: int = Query(..., description="Filter by workspace ID"),
    job_title: str | None = Query(None),
    company_name: str | None = Query(None),
    city: str | None = Query(None),
    education: str | None = Query(None),
    salary_min: float | None = Query(None),
    salary_max: float | None = Query(None),
    is_active: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List job records with filters and pagination."""
    filters = JobRecordFilter(
        job_title=job_title,
        company_name=company_name,
        city=city,
        education=education,
        salary_min=salary_min,
        salary_max=salary_max,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )
    records, total = await list_job_records(db, workspace_id, filters)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return ApiResponse(
        data=[JobRecordResponse.model_validate(r) for r in records],
        meta=PaginationMeta(total=total, page=page, page_size=page_size, total_pages=total_pages),
    )


@router.get("/stats", response_model=ApiResponse[JobRecordStatsResponse])
async def get_job_stats_api(
    workspace_id: int = Query(..., description="Filter by workspace ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregate statistics for job records."""
    stats = await get_job_stats(db, workspace_id)
    return ApiResponse(data=JobRecordStatsResponse(**stats))


@router.get("/{record_id}", response_model=ApiResponse[JobRecordResponse])
async def get_job_api(
    record_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get single job record by ID."""
    record = await get_job_record(db, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job record not found")
    return ApiResponse(data=JobRecordResponse.model_validate(record))
