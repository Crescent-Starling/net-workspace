from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import JSON_VARIANT
from app.models.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from app.models.source import Source
    from app.models.task import CrawlTask
    from app.models.workspace import Workspace


class JobRecord(CreatedAtMixin, Base):
    __tablename__ = "job_records"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "source_id",
            "source_job_id",
            name="uq_job_records_workspace_source_source_job_id",
        ),
        Index("ix_job_records_workspace_id", "workspace_id"),
        Index("ix_job_records_task_id", "task_id"),
        Index("ix_job_records_source_id", "source_id"),
        Index("ix_job_records_job_title", "job_title"),
        Index("ix_job_records_company_name", "company_name"),
        Index("ix_job_records_city", "city"),
        Index("ix_job_records_education", "education"),
        Index("ix_job_records_publish_date", "publish_date"),
        Index("ix_job_records_captured_at", "captured_at"),
        Index("ix_job_records_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("crawl_tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sources.id", ondelete="RESTRICT"),
        nullable=False,
    )
    source_job_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_url: Mapped[str] = mapped_column(Text, nullable=False)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    job_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    education: Mapped[str | None] = mapped_column(String(100), nullable=True)
    experience_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    salary_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    salary_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    salary_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    salary_currency: Mapped[str | None] = mapped_column(String(16), nullable=True)
    salary_period: Mapped[str | None] = mapped_column(String(32), nullable=True)
    publish_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    job_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    raw_data: Mapped[dict | list] = mapped_column(JSON_VARIANT, nullable=False)

    workspace: Mapped["Workspace"] = relationship(back_populates="job_records")
    task: Mapped["CrawlTask"] = relationship(back_populates="job_records")
    source: Mapped["Source"] = relationship(back_populates="job_records")

