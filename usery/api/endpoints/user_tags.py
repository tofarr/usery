from typing import List, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from usery.api.deps import get_current_user, get_db, get_current_superuser
from usery.api.schemas.user import User
from usery.api.schemas.tag import Tag
from usery.api.schemas.user_tag import UserTag, UserTagCreate
from usery.api.schemas.batch import BatchRequest, BatchResponse, BatchResponseItem, BatchOperationType
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
    
    # Check if tag requires superuser and current user is not a superuser
    if tag.requires_superuser and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This tag requires superuser privileges to assign",
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
    
    # Check if tag exists and requires superuser
    tag = await tag_service.get_tag(db, code=tag_code)
    if tag and tag.requires_superuser and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This tag requires superuser privileges to remove",
        )
    
    # Delete user tag
    user_tag = await user_tag_service.delete_user_tag(db, user_id=user_id, tag_code=tag_code)
    if not user_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have this tag",
        )
    
    return user_tag


@router.post("/batch", response_model=BatchResponse)
async def batch_user_tags_operations(
    *,
    db: AsyncSession = Depends(get_db),
    batch_request: BatchRequest[UserTagCreate],
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Perform batch operations on user tags (create, delete).
    """
    results = []
    success_count = 0
    error_count = 0

    for index, operation in enumerate(batch_request.operations):
        try:
            if operation.operation == BatchOperationType.CREATE:
                if not operation.data:
                    raise ValueError("Data is required for create operation")
                
                user_tag_data = operation.data
                user_id = user_tag_data.user_id
                tag_code = user_tag_data.tag_code
                
                # Check if user exists
                user = await user_service.get_user(db, user_id=user_id)
                if not user:
                    raise ValueError(f"User with ID {user_id} not found")
                
                # Check if current user is the requested user or a superuser
                if current_user.id != user_id and not current_user.is_superuser:
                    raise ValueError(f"Not enough permissions to modify user {user_id}'s tags")
                
                # Check if tag exists
                tag = await tag_service.get_tag(db, code=tag_code)
                if not tag:
                    raise ValueError(f"Tag with code {tag_code} not found")
                
                # Check if tag requires superuser and current user is not a superuser
                if tag.requires_superuser and not current_user.is_superuser:
                    raise ValueError(f"Tag {tag_code} requires superuser privileges to assign")
                
                # Check if user already has this tag
                user_tag = await user_tag_service.get_user_tag(db, user_id=user_id, tag_code=tag_code)
                if user_tag:
                    raise ValueError(f"User {user_id} already has tag {tag_code}")
                
                # Create user tag
                created_user_tag = await user_tag_service.create_user_tag(db, user_tag_in=user_tag_data)
                results.append(BatchResponseItem(
                    success=True,
                    data=created_user_tag,
                    index=index
                ))
                success_count += 1
                
            elif operation.operation == BatchOperationType.DELETE:
                if not operation.data:
                    raise ValueError("Data is required for delete operation")
                
                user_tag_data = operation.data
                user_id = user_tag_data.user_id
                tag_code = user_tag_data.tag_code
                
                # Check if user exists
                user = await user_service.get_user(db, user_id=user_id)
                if not user:
                    raise ValueError(f"User with ID {user_id} not found")
                
                # Check if current user is the requested user or a superuser
                if current_user.id != user_id and not current_user.is_superuser:
                    raise ValueError(f"Not enough permissions to modify user {user_id}'s tags")
                
                # Check if tag exists and requires superuser
                tag = await tag_service.get_tag(db, code=tag_code)
                if tag and tag.requires_superuser and not current_user.is_superuser:
                    raise ValueError(f"Tag {tag_code} requires superuser privileges to remove")
                
                # Delete user tag
                deleted_user_tag = await user_tag_service.delete_user_tag(db, user_id=user_id, tag_code=tag_code)
                if not deleted_user_tag:
                    raise ValueError(f"User {user_id} does not have tag {tag_code}")
                
                results.append(BatchResponseItem(
                    success=True,
                    data=deleted_user_tag,
                    index=index
                ))
                success_count += 1
                
            else:
                raise ValueError(f"Unknown or unsupported operation type: {operation.operation}")
                
        except Exception as e:
            results.append(BatchResponseItem(
                success=False,
                error=str(e),
                index=index
            ))
            error_count += 1
    
    return BatchResponse(
        results=results,
        success_count=success_count,
        error_count=error_count
    )