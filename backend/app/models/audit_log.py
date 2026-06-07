from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import JSON_VARIANT
from app.models.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from app.models.workspace import Workspace


class AuditLog(CreatedAtMixin, Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_workspace_id", "workspace_id"),
        Index("ix_audit_logs_actor_type_actor_id", "actor_type", "actor_id"),
        Index("ix_audit_logs_target_type_target_id", "target_type", "target_id"),
        Index("ix_audit_logs_action", "action"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    before_snapshot: Mapped[dict | list | None] = mapped_column(JSON_VARIANT, nullable=True)
    after_snapshot: Mapped[dict | list | None] = mapped_column(JSON_VARIANT, nullable=True)
    metadata_: Mapped[dict | list | None] = mapped_column("metadata", JSON_VARIANT, nullable=True)

    workspace: Mapped["Workspace | None"] = relationship(back_populates="audit_logs")

