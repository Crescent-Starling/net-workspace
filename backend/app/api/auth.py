from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import create_access_token, get_current_user, get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, UserLogin, UserRegister, UserResponse
from app.schemas.common import ApiResponse
from app.schemas.workspace import WorkspaceCreate
from app.services import auth_service
from app.services.workspace_service import create_workspace

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=ApiResponse[UserResponse])
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    # Check username uniqueness
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )
    # Check email uniqueness
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = await auth_service.register_user(db, data)
    await db.flush()

    # Auto-create a default workspace
    await create_workspace(db, user.id, WorkspaceCreate(name="My Workspace"))
    await db.flush()

    token = create_access_token(data={"sub": str(user.id)})
    return ApiResponse(
        data=UserResponse.model_validate(user),
        message="Registration successful",
    )


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT token."""
    user = await auth_service.authenticate_user(db, data.username, data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token = create_access_token(data={"sub": str(user.id)})
    return ApiResponse(
        data=TokenResponse(access_token=token),
        message="Login successful",
    )


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Get current authenticated user info."""
    return ApiResponse(data=UserResponse.model_validate(current_user))
