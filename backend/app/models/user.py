from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.onboarding import OnboardingRequest
    from app.models.proposal import Proposal
    from app.models.task import CrawlTask
    from app.models.template import TemplateVersion
    from app.models.workspace import Workspace


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_role_status", "role", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)

    workspaces: Mapped[list["Workspace"]] = relationship(back_populates="user")
    template_versions_created: Mapped[list["TemplateVersion"]] = relationship(
        back_populates="created_by_user",
        foreign_keys="TemplateVersion.created_by_user_id",
    )
    onboarding_requests_submitted: Mapped[list["OnboardingRequest"]] = relationship(
        back_populates="submitted_by_user",
        foreign_keys="OnboardingRequest.submitted_by_user_id",
    )
    crawl_tasks_created: Mapped[list["CrawlTask"]] = relationship(
        back_populates="created_by_user",
        foreign_keys="CrawlTask.created_by_user_id",
    )
    proposals_submitted: Mapped[list["Proposal"]] = relationship(
        back_populates="submitted_by_user",
        foreign_keys="Proposal.submitted_by_user_id",
    )
    proposals_reviewed: Mapped[list["Proposal"]] = relationship(
        back_populates="reviewed_by_user",
        foreign_keys="Proposal.reviewed_by_user_id",
    )

