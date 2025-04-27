from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from usery.api.deps import get_current_user, get_db, get_current_superuser
from usery.api.schemas.user_attribute import UserAttribute, UserAttributeCreate, UserAttributeUpdate
from usery.api.schemas.user import User
from usery.services import user_attribute as user_attribute_service
from usery.services import attribute as attribute_service
from usery.services import user as user_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/user-attributes", response_model=List[UserAttribute])
async def read_user_attributes(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve user attributes.
    """
    # Only superusers can see all user attributes
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access all user attributes",
        )
    
    user_attributes = await user_attribute_service.get_user_attributes(db, skip=skip, limit=limit)
    return user_attributes


@router.post("/user-attributes", response_model=UserAttribute)
async def create_user_attribute(
    user_attribute_in: UserAttributeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create new user attribute.
    """
    # Check if current user is superuser or the user is creating their own attribute
    if not current_user.is_superuser and current_user.id != user_attribute_in.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create user attributes for other users",
        )
    
    # Check if user exists
    user = await user_service.get_user(db, id=user_attribute_in.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check if attribute exists
    attribute = await attribute_service.get_attribute(db, id=user_attribute_in.attribute_id)
    if not attribute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attribute not found",
        )
    
    # Check if attribute requires superuser and current user is not a superuser
    if attribute.requires_superuser and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This attribute requires superuser privileges to assign",
        )
    
    # Check if user attribute already exists
    existing_user_attribute = await user_attribute_service.get_user_attribute_by_user_and_attribute(
        db, user_id=user_attribute_in.user_id, attribute_id=user_attribute_in.attribute_id
    )
    if existing_user_attribute:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User attribute already exists",
        )
    
    return await user_attribute_service.create_user_attribute(db, user_attribute_in=user_attribute_in)


@router.get("/user-attributes/{id}", response_model=UserAttribute)
async def read_user_attribute(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user attribute by id.
    """
    user_attribute = await user_attribute_service.get_user_attribute(db, id=id)
    if not user_attribute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User attribute not found",
        )
    
    # Check if current user is superuser or the user is accessing their own attribute
    if not current_user.is_superuser and current_user.id != user_attribute.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this user attribute",
        )
    
    return user_attribute


@router.put("/user-attributes/{id}", response_model=UserAttribute)
async def update_user_attribute(
    id: UUID,
    user_attribute_in: UserAttributeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a user attribute.
    """
    user_attribute = await user_attribute_service.get_user_attribute(db, id=id)
    if not user_attribute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User attribute not found",
        )
    
    # Check if current user is superuser or the user is updating their own attribute
    if not current_user.is_superuser and current_user.id != user_attribute.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this user attribute",
        )
    
    # Check if attribute requires superuser
    attribute = await attribute_service.get_attribute(db, id=user_attribute.attribute_id)
    if attribute and attribute.requires_superuser and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This attribute requires superuser privileges to modify",
        )
    
    user_attribute = await user_attribute_service.update_user_attribute(
        db, id=id, user_attribute_in=user_attribute_in
    )
    return user_attribute


@router.delete("/user-attributes/{id}", response_model=UserAttribute)
async def delete_user_attribute(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a user attribute.
    """
    user_attribute = await user_attribute_service.get_user_attribute(db, id=id)
    if not user_attribute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User attribute not found",
        )
    
    # Check if current user is superuser or the user is deleting their own attribute
    if not current_user.is_superuser and current_user.id != user_attribute.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this user attribute",
        )
    
    # Check if attribute requires superuser
    attribute = await attribute_service.get_attribute(db, id=user_attribute.attribute_id)
    if attribute and attribute.requires_superuser and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This attribute requires superuser privileges to remove",
        )
    
    user_attribute = await user_attribute_service.delete_user_attribute(db, id=id)
    return user_attribute


@router.get("/users/{user_id}/attributes", response_model=List[UserAttribute])
async def read_user_attributes_by_user(
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all attributes for a specific user.
    """
    # Check if current user is superuser or the user is accessing their own attributes
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access attributes for this user",
        )
    
    # Check if user exists
    user = await user_service.get_user(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    user_attributes = await user_attribute_service.get_user_attributes_by_user(
        db, user_id=user_id, skip=skip, limit=limit
    )
    return user_attributes


@router.get("/attributes/{attribute_id}/users", response_model=List[UserAttribute])
async def read_user_attributes_by_attribute(
    attribute_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all user attributes for a specific attribute.
    """
    # Only superusers can see all users with a specific attribute
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access all users with this attribute",
        )
    
    # Check if attribute exists
    attribute = await attribute_service.get_attribute(db, id=attribute_id)
    if not attribute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attribute not found",
        )
    
    user_attributes = await user_attribute_service.get_user_attributes_by_attribute(
        db, attribute_id=attribute_id, skip=skip, limit=limit
    )
    return user_attributes