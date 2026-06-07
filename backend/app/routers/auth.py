"""Auth router placeholder."""

from fastapi import APIRouter

router = APIRouter(tags=["auth"])


@router.get("")
async def auth_placeholder() -> dict[str, str]:
    return {"message": "not implemented yet"}


@router.post("/token")
async def login_placeholder() -> dict[str, str]:
    return {"message": "not implemented yet"}
