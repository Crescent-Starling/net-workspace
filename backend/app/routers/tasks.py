"""Tasks router placeholder."""

from fastapi import APIRouter

router = APIRouter(tags=["tasks"])


@router.get("")
async def tasks_placeholder() -> dict[str, str]:
    return {"message": "not implemented yet"}
