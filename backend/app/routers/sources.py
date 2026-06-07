"""Sources router placeholder."""

from fastapi import APIRouter

router = APIRouter(tags=["sources"])


@router.get("")
async def sources_placeholder() -> dict[str, str]:
    return {"message": "not implemented yet"}
