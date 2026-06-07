from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SourceCreate(BaseModel):
    source_name: str
    domain: str
    source_type: str
    content_type: str
    site_locale: str | None = None


class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_name: str
    domain: str
    source_type: str
    content_type: str
    site_locale: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime


SourceResponse.model_rebuild()
