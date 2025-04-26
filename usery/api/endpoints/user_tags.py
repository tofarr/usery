from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from usery.api.deps import get_current_user, get_db
from usery.api.schemas.user import User
from usery.api.schemas.tag import Tag
from usery.api.schemas.user_tag import UserTag, UserTagCreate
from usery.services import user_tag as user_tag_service
from usery.services import tag as tag_service
from usery.services import user as user_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/users/{user_id}/tags", response_model=List[Tag])
async def read_user_tags(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve tags for a user.
    """
    # Check if user exists
    user = await user_service.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check if current user is the requested user or a superuser
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this user's tags",
        )
    
    # Get user tags
    user_tags = await user_tag_service.get_user_tags_with_details(db, user_id=user_id)
    return [item["tag"] for item in user_tags]


@router.post("/users/{user_id}/tags", response_model=UserTag)
async def add_user_tag(
    user_id: UUID,
    tag_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add a tag to a user.
    """
    # Check if user exists
    user = await user_service.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check if current user is the requested user or a superuser
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to modify this user's tags",
        )
    
    # Check if tag exists
    tag = await tag_service.get_tag(db, code=tag_code)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )
    
    # Check if user already has this tag
    user_tag = await user_tag_service.get_user_tag(db, user_id=user_id, tag_code=tag_code)
    if user_tag:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has this tag",
        )
    
    # Create user tag
    user_tag_in = UserTagCreate(user_id=user_id, tag_code=tag_code)
    return await user_tag_service.create_user_tag(db, user_tag_in=user_tag_in)


@router.delete("/users/{user_id}/tags/{tag_code}", response_model=UserTag)
async def remove_user_tag(
    user_id: UUID,
    tag_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Remove a tag from a user.
    """
    # Check if user exists
    user = await user_service.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check if current user is the requested user or a superuser
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to modify this user's tags",
        )
    
    # Delete user tag
    user_tag = await user_tag_service.delete_user_tag(db, user_id=user_id, tag_code=tag_code)
    if not user_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have this tag",
        )
    
    return user_tag