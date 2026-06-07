"""Templates router placeholder."""

from fastapi import APIRouter

router = APIRouter(tags=["templates"])


@router.get("")
async def templates_placeholder() -> dict[str, str]:
    return {"message": "not implemented yet"}
