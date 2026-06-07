from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class OnboardingRequestCreate(BaseModel):
    """Payload to submit a new site onboarding request."""

    source_id: Optional[int] = None
    target_url: str = Field(..., max_length=65535)
    content_type_hint: Optional[str] = Field(default=None, max_length=32)


class OnboardingRequestResponse(BaseModel):
    """Onboarding request representation."""

    id: int
    workspace_id: int
    source_id: Optional[int] = None
    submitted_by_user_id: int
    target_url: str
    content_type_hint: Optional[str] = None
    status: str
    site_guess: Optional[str] = None
    render_mode_guess: Optional[str] = None
    risk_flags: Optional[Any] = None
    analysis_summary: Optional[Any] = None
    published_template_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
