from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import JSON_VARIANT
from app.models.mixins import CreatedAtMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.onboarding import OnboardingRequest, TemplateTestRun
    from app.models.source import Source
    from app.models.task import CrawlTask
    from app.models.user import User
    from app.models.workspace import Workspace


class Template(TimestampMixin, Base):
    __tablename__ = "templates"
    __table_args__ = (
        UniqueConstraint("workspace_id", "template_name", name="uq_templates_workspace_template_name"),
        UniqueConstraint(
            "source_id",
            "template_name",
            "template_scope",
            name="uq_templates_source_template_name_template_scope",
        ),
        Index("ix_templates_workspace_id", "workspace_id"),
        Index("ix_templates_source_id", "source_id"),
        Index("ix_templates_template_scope_status", "template_scope", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sources.id", ondelete="RESTRICT"),
        nullable=False,
    )
    template_name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    template_scope: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    current_version_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "template_versions.id",
            name="fk_templates_current_version_id_template_versions",
            use_alter=True,
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    workspace: Mapped["Workspace | None"] = relationship(back_populates="templates")
    source: Mapped["Source"] = relationship(back_populates="templates")
    versions: Mapped[list["TemplateVersion"]] = relationship(
        back_populates="template",
        foreign_keys="TemplateVersion.template_id",
        cascade="all, delete-orphan",
    )
    current_version: Mapped["TemplateVersion | None"] = relationship(
        foreign_keys=[current_version_id],
        post_update=True,
    )
    published_onboarding_requests: Mapped[list["OnboardingRequest"]] = relationship(
        back_populates="published_template",
        foreign_keys="OnboardingRequest.published_template_id",
    )


class TemplateVersion(CreatedAtMixin, Base):
    __tablename__ = "template_versions"
    __table_args__ = (
        UniqueConstraint("template_id", "version", name="uq_template_versions_template_id_version"),
        Index("ix_template_versions_template_id", "template_id"),
        Index("ix_template_versions_generation_source", "generation_source"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    dsl_content: Mapped[dict] = mapped_column(JSON_VARIANT, nullable=False)
    generation_source: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    template: Mapped["Template"] = relationship(
        back_populates="versions",
        foreign_keys=[template_id],
    )
    created_by_user: Mapped["User | None"] = relationship(back_populates="template_versions_created")
    test_runs: Mapped[list["TemplateTestRun"]] = relationship(back_populates="template_version")
    crawl_tasks: Mapped[list["CrawlTask"]] = relationship(back_populates="template_version")

