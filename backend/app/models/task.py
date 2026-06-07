from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import JSON_VARIANT
from app.models.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from app.models.job_record import JobRecord
    from app.models.task import TaskRunLog
    from app.models.template import TemplateVersion
    from app.models.user import User
    from app.models.workspace import Workspace


class CrawlTask(CreatedAtMixin, Base):
    __tablename__ = "crawl_tasks"
    __table_args__ = (
        Index("ix_crawl_tasks_workspace_id", "workspace_id"),
        Index("ix_crawl_tasks_template_version_id", "template_version_id"),
        Index("ix_crawl_tasks_task_status", "task_status"),
        Index("ix_crawl_tasks_scheduled_at", "scheduled_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    template_version_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("template_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_by_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_name: Mapped[str] = mapped_column(String(150), nullable=False)
    task_status: Mapped[str] = mapped_column(String(32), nullable=False)
    task_params: Mapped[dict] = mapped_column(JSON_VARIANT, nullable=False)
    schedule_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    workspace: Mapped["Workspace"] = relationship(back_populates="crawl_tasks")
    template_version: Mapped["TemplateVersion"] = relationship(back_populates="crawl_tasks")
    created_by_user: Mapped["User"] = relationship(back_populates="crawl_tasks_created")
    logs: Mapped[list["TaskRunLog"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    job_records: Mapped[list["JobRecord"]] = relationship(back_populates="task")


class TaskRunLog(CreatedAtMixin, Base):
    __tablename__ = "task_run_logs"
    __table_args__ = (
        Index("ix_task_run_logs_task_id", "task_id"),
        Index("ix_task_run_logs_log_level", "log_level"),
        Index("ix_task_run_logs_event_type", "event_type"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("crawl_tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    log_level: Mapped[str] = mapped_column(String(16), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict | list | None] = mapped_column(JSON_VARIANT, nullable=True)

    task: Mapped["CrawlTask"] = relationship(back_populates="logs")

