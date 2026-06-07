"""Workspaces router placeholder."""

from fastapi import APIRouter

router = APIRouter(tags=["workspaces"])


@router.get("")
async def workspaces_placeholder() -> dict[str, str]:
    return {"message": "not implemented yet"}
