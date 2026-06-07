from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer


class JobRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    task_id: int
    source_id: int
    source_job_id: str | None = None
    job_url: str
    job_title: str
    job_category: str | None = None
    company_name: str | None = None
    city: str | None = None
    education: str | None = None
    experience_text: str | None = None
    salary_text: str | None = None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    salary_currency: str | None = None
    salary_period: str | None = None
    publish_date: date | None = None
    job_description: str | None = None
    captured_at: datetime
    first_seen_at: datetime
    last_seen_at: datetime
    is_active: bool
    raw_data: dict | list

    @field_serializer("salary_min", "salary_max")
    def serialize_decimal(self, v: Decimal | None) -> float | None:
        if v is None:
            return None
        return float(v)


class JobRecordFilter(BaseModel):
    job_title: str | None = None
    company_name: str | None = None
    city: str | None = None
    education: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    is_active: bool = True
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class JobRecordStatsResponse(BaseModel):
    total_count: int
    avg_salary_min: float | None = None
    avg_salary_max: float | None = None
    city_distribution: dict[str, int] = {}
    category_distribution: dict[str, int] = {}


JobRecordResponse.model_rebuild()
