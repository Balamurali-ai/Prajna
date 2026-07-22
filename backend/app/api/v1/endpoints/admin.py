"""
====================================================
API v1 - Admin (User Management)
====================================================
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.database.models.user import UserRole, UserStatus
from app.middleware.auth import get_current_user, require_admin
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=List[UserResponse], summary="List all users")
async def list_users(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    repo = UserRepository(db)
    users = await repo.list_all(skip=skip, limit=limit)
    return [UserResponse.model_validate(u) for u in users]


@router.get("/users/{user_id}", response_model=UserResponse, summary="Get user by ID")
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return UserResponse.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserResponse, summary="Update user")
async def update_user(
    user_id: UUID,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    allowed = {"full_name", "role", "status", "department", "badge_number", "jurisdiction"}
    for key, value in payload.items():
        if key in allowed:
            if key == "role":
                value = UserRole(value)
            elif key == "status":
                value = UserStatus(value)
            setattr(user, key, value)

    user = await repo.update(user)
    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}", status_code=204, summary="Delete user")
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    repo = UserRepository(db)
    await repo.soft_delete(user_id)
