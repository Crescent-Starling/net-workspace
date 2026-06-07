from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    """Audit log entry representation."""

    id: int
    workspace_id: Optional[int] = None
    actor_type: str
    actor_id: Optional[int] = None
    action: str
    target_type: str
    target_id: int
    before_snapshot: Optional[Any] = None
    after_snapshot: Optional[Any] = None
    metadata: Optional[Any] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
