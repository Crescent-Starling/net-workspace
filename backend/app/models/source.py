from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.job_record import JobRecord
    from app.models.onboarding import OnboardingRequest
    from app.models.template import Template


class Source(TimestampMixin, Base):
    __tablename__ = "sources"
    __table_args__ = (
        Index("ix_sources_source_type_status", "source_type", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content_type: Mapped[str] = mapped_column(String(32), nullable=False)
    site_locale: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)

    templates: Mapped[list["Template"]] = relationship(back_populates="source")
    onboarding_requests: Mapped[list["OnboardingRequest"]] = relationship(back_populates="source")
    job_records: Mapped[list["JobRecord"]] = relationship(back_populates="source")

