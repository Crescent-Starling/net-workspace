from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.job_record import JobRecord
    from app.models.onboarding import OnboardingRequest
    from app.models.proposal import Proposal
    from app.models.task import CrawlTask
    from app.models.template import Template
    from app.models.user import User


class Workspace(TimestampMixin, Base):
    __tablename__ = "workspaces"
    __table_args__ = (
        Index("ix_workspaces_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)

    user: Mapped["User"] = relationship(back_populates="workspaces")
    templates: Mapped[list["Template"]] = relationship(back_populates="workspace")
    onboarding_requests: Mapped[list["OnboardingRequest"]] = relationship(back_populates="workspace")
    crawl_tasks: Mapped[list["CrawlTask"]] = relationship(back_populates="workspace")
    job_records: Mapped[list["JobRecord"]] = relationship(back_populates="workspace")
    proposals: Mapped[list["Proposal"]] = relationship(back_populates="workspace")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="workspace")
