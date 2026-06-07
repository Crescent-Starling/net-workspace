from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_record import JobRecord

if TYPE_CHECKING:
    from app.schemas.job_record import JobRecordFilter


async def list_job_records(
    db: AsyncSession,
    workspace_id: int,
    filters: "JobRecordFilter",
) -> tuple[list[JobRecord], int]:
    """List job records with filters and pagination."""
    query = select(JobRecord).where(
        JobRecord.workspace_id == workspace_id,
        JobRecord.is_active == filters.is_active,
    )
    count_query = (
        select(func.count())
        .select_from(JobRecord)
        .where(
            JobRecord.workspace_id == workspace_id,
            JobRecord.is_active == filters.is_active,
        )
    )

    if filters.job_title is not None:
        query = query.where(JobRecord.job_title.ilike(f"%{filters.job_title}%"))
        count_query = count_query.where(JobRecord.job_title.ilike(f"%{filters.job_title}%"))
    if filters.company_name is not None:
        query = query.where(JobRecord.company_name.ilike(f"%{filters.company_name}%"))
        count_query = count_query.where(
            JobRecord.company_name.ilike(f"%{filters.company_name}%")
        )
    if filters.city is not None:
        query = query.where(JobRecord.city == filters.city)
        count_query = count_query.where(JobRecord.city == filters.city)
    if filters.education is not None:
        query = query.where(JobRecord.education == filters.education)
        count_query = count_query.where(JobRecord.education == filters.education)
    if filters.salary_min is not None:
        query = query.where(JobRecord.salary_max >= filters.salary_min)
    if filters.salary_max is not None:
        query = query.where(JobRecord.salary_min <= filters.salary_max)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(
        query.order_by(JobRecord.captured_at.desc())
        .offset(filters.offset)
        .limit(filters.page_size)
    )
    return list(result.scalars().all()), total


async def get_job_record(
    db: AsyncSession, record_id: int
) -> JobRecord | None:
    """Get single job record by ID."""
    result = await db.execute(select(JobRecord).where(JobRecord.id == record_id))
    return result.scalar_one_or_none()


async def get_job_stats(db: AsyncSession, workspace_id: int) -> dict:
    """Get aggregate stats for job records."""
    base = JobRecord.workspace_id == workspace_id
    base_active = base & (JobRecord.is_active == True)

    # Total count
    total = (await db.execute(
        select(func.count()).select_from(JobRecord).where(base_active)
    )).scalar() or 0

    # Average salary
    avg_min = (await db.execute(
        select(func.avg(JobRecord.salary_min)).where(base_active)
    )).scalar()
    avg_max = (await db.execute(
        select(func.avg(JobRecord.salary_max)).where(base_active)
    )).scalar()

    # City distribution
    city_rows = (await db.execute(
        select(JobRecord.city, func.count().label("cnt"))
        .where(base_active)
        .group_by(JobRecord.city)
        .order_by(func.count().desc())
        .limit(20)
    )).all()

    # Category distribution
    cat_rows = (await db.execute(
        select(JobRecord.job_category, func.count().label("cnt"))
        .where(base_active)
        .group_by(JobRecord.job_category)
        .order_by(func.count().desc())
        .limit(20)
    )).all()

    return {
        "total_count": total,
        "avg_salary_min": float(avg_min) if avg_min else None,
        "avg_salary_max": float(avg_max) if avg_max else None,
        "city_distribution": {r[0]: r[1] for r in city_rows if r[0]},
        "category_distribution": {r[0]: r[1] for r in cat_rows if r[0]},
    }
