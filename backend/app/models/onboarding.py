from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import JSON_VARIANT
from app.models.mixins import CreatedAtMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.source import Source
    from app.models.template import Template, TemplateVersion
    from app.models.user import User
    from app.models.workspace import Workspace


class OnboardingRequest(TimestampMixin, Base):
    __tablename__ = "onboarding_requests"
    __table_args__ = (
        Index("ix_onboarding_requests_workspace_id", "workspace_id"),
        Index("ix_onboarding_requests_submitted_by_user_id", "submitted_by_user_id"),
        Index("ix_onboarding_requests_status", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    submitted_by_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_url: Mapped[str] = mapped_column(Text, nullable=False)
    content_type_hint: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    site_guess: Mapped[str | None] = mapped_column(String(64), nullable=True)
    render_mode_guess: Mapped[str | None] = mapped_column(String(32), nullable=True)
    risk_flags: Mapped[list | dict | None] = mapped_column(JSON_VARIANT, nullable=True)
    analysis_summary: Mapped[dict | None] = mapped_column(JSON_VARIANT, nullable=True)
    published_template_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("templates.id", ondelete="SET NULL"),
        nullable=True,
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="onboarding_requests")
    source: Mapped["Source | None"] = relationship(back_populates="onboarding_requests")
    submitted_by_user: Mapped["User"] = relationship(back_populates="onboarding_requests_submitted")
    published_template: Mapped["Template | None"] = relationship(
        back_populates="published_onboarding_requests",
        foreign_keys=[published_template_id],
    )
    template_test_runs: Mapped[list["TemplateTestRun"]] = relationship(back_populates="onboarding_request")


class TemplateTestRun(CreatedAtMixin, Base):
    __tablename__ = "template_test_runs"
    __table_args__ = (
        Index("ix_template_test_runs_template_version_id", "template_version_id"),
        Index("ix_template_test_runs_onboarding_request_id", "onboarding_request_id"),
        Index("ix_template_test_runs_test_status", "test_status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    template_version_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("template_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    onboarding_request_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("onboarding_requests.id", ondelete="SET NULL"),
        nullable=True,
    )
    test_url: Mapped[str] = mapped_column(Text, nullable=False)
    test_status: Mapped[str] = mapped_column(String(32), nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    items_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    detail_success_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    field_completeness: Mapped[dict | None] = mapped_column(JSON_VARIANT, nullable=True)
    sample_result: Mapped[dict | list | None] = mapped_column(JSON_VARIANT, nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    template_version: Mapped["TemplateVersion"] = relationship(back_populates="test_runs")
    onboarding_request: Mapped["OnboardingRequest | None"] = relationship(back_populates="template_test_runs")

