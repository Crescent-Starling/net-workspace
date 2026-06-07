"""Job records router placeholder."""

from fastapi import APIRouter

router = APIRouter(tags=["job_records"])


@router.get("")
async def job_records_placeholder() -> dict[str, str]:
    return {"message": "not implemented yet"}
