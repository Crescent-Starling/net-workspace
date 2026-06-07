from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProposalCreate(BaseModel):
    """Payload to create a proposal (review request, etc.)."""

    proposal_type: str = Field(..., max_length=32)
    target_type: str = Field(..., max_length=32)
    target_id: int
    title: str = Field(..., max_length=255)
    description: Optional[str] = Field(default=None, max_length=65535)


class ProposalResponse(BaseModel):
    """Proposal representation."""

    id: int
    workspace_id: int
    submitted_by_user_id: int
    proposal_type: str
    target_type: str
    target_id: int
    title: str
    description: Optional[str] = None
    review_status: str
    reviewed_by_user_id: Optional[int] = None
    review_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
