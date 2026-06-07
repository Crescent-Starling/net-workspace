from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class TemplateCreate(BaseModel):
    source_id: int
    template_name: str
    display_name: str
    template_scope: str = "personal"
    dsl_content: dict[str, Any]  # Initial DSL for first version


class TemplateUpdate(BaseModel):
    display_name: str | None = None
    status: str | None = None


class TemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int | None = None
    source_id: int
    template_name: str
    display_name: str
    template_scope: str
    status: str
    current_version_id: int | None = None
    created_at: datetime
    updated_at: datetime


class TemplateVersionCreate(BaseModel):
    dsl_content: dict[str, Any]
    generation_source: str
    confidence_level: str | None = None
    change_summary: str | None = None


class TemplateVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    template_id: int
    version: str
    dsl_content: dict[str, Any]
    generation_source: str
    confidence_level: str | None = None
    change_summary: str | None = None
    created_by_user_id: int | None = None
    created_at: datetime


class TemplateDetailResponse(TemplateResponse):
    current_version: TemplateVersionResponse | None = None


TemplateResponse.model_rebuild()
TemplateVersionResponse.model_rebuild()
TemplateDetailResponse.model_rebuild()
