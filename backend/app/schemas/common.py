from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, field_serializer

T = TypeVar("T")


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def total_pages(self, total: int) -> int:
        return (total + self.page_size - 1) // self.page_size


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str | None = None
    meta: PaginationMeta | None = None


def _serialize_decimal(v: Decimal | None) -> float | None:
    if v is None:
        return None
    return float(v)
