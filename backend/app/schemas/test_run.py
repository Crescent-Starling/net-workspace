from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class TemplateTestRunResponse(BaseModel):
    """Template test-run representation."""

    id: int
    template_version_id: int
    onboarding_request_id: Optional[int] = None
    test_url: str
    test_status: str
    sample_size: int
    items_found: int
    detail_success_rate: Optional[float] = None
    field_completeness: Optional[Any] = None
    sample_result: Optional[Any] = None
    error_summary: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
