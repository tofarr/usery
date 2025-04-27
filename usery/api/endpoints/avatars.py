from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from usery.api.deps import get_current_active_user
from usery.api.schemas.avatar import AvatarUpdate
from usery.api.schemas.user import User
from usery.db.session import get_db
from usery.models.user import User as UserModel
from usery.services.user import get_user, update_user

router = APIRouter()


@router.put("/{user_id}", response_model=User)
async def update_avatar(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
    avatar_update: AvatarUpdate,
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Update a user's avatar.
    
    Users can update their own avatar.
    Superusers can update any user's avatar.
    """
    user = await get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check if the current user has permission to update this user's avatar
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this user's avatar",
        )
    
    # Update the user's avatar
    from usery.api.schemas.user import UserUpdate
    user_update = UserUpdate(avatar_url=avatar_update.avatar_url)
    updated_user = await update_user(db, user_id=user_id, user_in=user_update)
    
    return updated_user


@router.delete("/{user_id}", response_model=User)
async def remove_avatar(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Remove a user's avatar.
    
    Users can remove their own avatar.
    Superusers can remove any user's avatar.
    """
    user = await get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check if the current user has permission to remove this user's avatar
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to remove this user's avatar",
        )
    
    # Remove the user's avatar
    from usery.api.schemas.user import UserUpdate
    user_update = UserUpdate(avatar_url=None)
    updated_user = await update_user(db, user_id=user_id, user_in=user_update)
    
    return updated_user