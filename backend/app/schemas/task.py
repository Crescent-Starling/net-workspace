from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    template_version_id: int
    task_name: str
    task_params: dict[str, Any]
    schedule_type: str | None = None
    scheduled_at: datetime | None = None


class TaskUpdate(BaseModel):
    task_status: str | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    template_version_id: int
    created_by_user_id: int
    task_name: str
    task_status: str
    task_params: dict[str, Any]
    schedule_type: str | None = None
    scheduled_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    total_records: int
    error_summary: str | None = None
    created_at: datetime


class TaskRunLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    log_level: str
    event_type: str
    message: str
    payload: dict | list | None = None
    created_at: datetime


class TaskDetailResponse(TaskResponse):
    logs: list[TaskRunLogResponse] = []


TaskResponse.model_rebuild()
TaskRunLogResponse.model_rebuild()
TaskDetailResponse.model_rebuild()
