from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WorkspaceCreate(BaseModel):
    name: str
    description: str | None = None


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    slug: str
    description: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime


WorkspaceResponse.model_rebuild()
