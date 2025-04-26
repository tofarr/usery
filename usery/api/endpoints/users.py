from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from usery.api.deps import get_current_active_user
from usery.api.schemas.user import User, UserCreate, UserUpdate, UserWithTags
from usery.db.session import get_db
from usery.models.user import User as UserModel
from usery.services.user import (
    create_user,
    delete_user,
    get_user,
    get_user_by_email,
    get_user_by_username,
    get_users,
    update_user,
    get_user_with_tags,
)

router = APIRouter()


@router.get("/", response_model=List[User])
async def read_users(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve users.
    """
    users = await get_users(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_new_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create new user.
    """
    user = await get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    
    user = await get_user_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this username already exists in the system.",
        )
    
    user = await create_user(db, user_in=user_in)
    return user


@router.get("/{user_id}", response_model=User)
async def read_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
) -> Any:
    """
    Get a specific user by id.
    """
    user = await get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.get("/{user_id}/with-tags", response_model=UserWithTags)
async def read_user_with_tags(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Get a specific user by id with their tags.
    """
    result = await get_user_with_tags(db, user_id=user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return UserWithTags(
        id=result["user"].id,
        email=result["user"].email,
        username=result["user"].username,
        full_name=result["user"].full_name,
        is_active=result["user"].is_active,
        created_at=result["user"].created_at,
        updated_at=result["user"].updated_at,
        tags=result["tags"]
    )


@router.put("/{user_id}", response_model=User)
async def update_user_info(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
    user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """
    user = await get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if user_in.email is not None and user_in.email != user.email:
        existing_user = await get_user_by_email(db, email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
    
    if user_in.username is not None and user_in.username != user.username:
        existing_user = await get_user_by_username(db, username=user_in.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )
    
    user = await update_user(db, user_id=user_id, user_in=user_in)
    return user


@router.delete("/{user_id}", response_model=User)
async def delete_user_by_id(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
) -> Any:
    """
    Delete a user.
    """
    user = await get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    user = await delete_user(db, user_id=user_id)
    return user