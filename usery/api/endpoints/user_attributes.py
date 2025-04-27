from typing import List, Optional, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from usery.api.deps import get_current_user, get_db, get_current_superuser
from usery.api.schemas.user_attribute import UserAttribute, UserAttributeCreate, UserAttributeUpdate
from usery.api.schemas.user import User
from usery.api.schemas.batch import BatchRequest, BatchResponse, BatchResponseItem, BatchOperationType
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


@router.post("/batch", response_model=BatchResponse)
async def batch_user_attributes_operations(
    *,
    db: AsyncSession = Depends(get_db),
    batch_request: BatchRequest[UserAttributeCreate | UserAttributeUpdate],
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Perform batch operations on user attributes (create, update, delete).
    """
    results = []
    success_count = 0
    error_count = 0

    for index, operation in enumerate(batch_request.operations):
        try:
            if operation.operation == BatchOperationType.CREATE:
                if not operation.data:
                    raise ValueError("Data is required for create operation")
                
                user_attribute_data = operation.data
                user_id = user_attribute_data.user_id
                attribute_id = user_attribute_data.attribute_id
                
                # Check if user exists
                user = await user_service.get_user(db, user_id=user_id)
                if not user:
                    raise ValueError(f"User with ID {user_id} not found")
                
                # Check if current user is the requested user or a superuser
                if current_user.id != user_id and not current_user.is_superuser:
                    raise ValueError(f"Not enough permissions to modify user {user_id}'s attributes")
                
                # Check if attribute exists
                attribute = await attribute_service.get_attribute(db, id=attribute_id)
                if not attribute:
                    raise ValueError(f"Attribute with ID {attribute_id} not found")
                
                # Check if attribute requires superuser and current user is not a superuser
                if attribute.requires_superuser and not current_user.is_superuser:
                    raise ValueError(f"Attribute {attribute_id} requires superuser privileges to assign")
                
                # Check if user attribute already exists
                existing_user_attribute = await user_attribute_service.get_user_attribute_by_user_and_attribute(
                    db, user_id=user_id, attribute_id=attribute_id
                )
                if existing_user_attribute:
                    raise ValueError(f"User {user_id} already has attribute {attribute_id}")
                
                # Create user attribute
                created_user_attribute = await user_attribute_service.create_user_attribute(
                    db, user_attribute_in=user_attribute_data
                )
                results.append(BatchResponseItem(
                    success=True,
                    data=created_user_attribute,
                    index=index
                ))
                success_count += 1
                
            elif operation.operation == BatchOperationType.UPDATE:
                if not operation.id:
                    raise ValueError("ID is required for update operation")
                if not operation.data:
                    raise ValueError("Data is required for update operation")
                
                user_attribute_id = operation.id
                user_attribute_data = operation.data
                
                # Check if user attribute exists
                user_attribute = await user_attribute_service.get_user_attribute(db, id=user_attribute_id)
                if not user_attribute:
                    raise ValueError(f"User attribute with ID {user_attribute_id} not found")
                
                # Check if current user is the user who owns the attribute or a superuser
                if current_user.id != user_attribute.user_id and not current_user.is_superuser:
                    raise ValueError(f"Not enough permissions to update this user attribute")
                
                # Check if attribute requires superuser
                attribute = await attribute_service.get_attribute(db, id=user_attribute.attribute_id)
                if attribute and attribute.requires_superuser and not current_user.is_superuser:
                    raise ValueError(f"Attribute {attribute.id} requires superuser privileges to modify")
                
                # Update user attribute
                updated_user_attribute = await user_attribute_service.update_user_attribute(
                    db, id=user_attribute_id, user_attribute_in=user_attribute_data
                )
                results.append(BatchResponseItem(
                    success=True,
                    data=updated_user_attribute,
                    index=index
                ))
                success_count += 1
                
            elif operation.operation == BatchOperationType.DELETE:
                if not operation.id:
                    raise ValueError("ID is required for delete operation")
                
                user_attribute_id = operation.id
                
                # Check if user attribute exists
                user_attribute = await user_attribute_service.get_user_attribute(db, id=user_attribute_id)
                if not user_attribute:
                    raise ValueError(f"User attribute with ID {user_attribute_id} not found")
                
                # Check if current user is the user who owns the attribute or a superuser
                if current_user.id != user_attribute.user_id and not current_user.is_superuser:
                    raise ValueError(f"Not enough permissions to delete this user attribute")
                
                # Check if attribute requires superuser
                attribute = await attribute_service.get_attribute(db, id=user_attribute.attribute_id)
                if attribute and attribute.requires_superuser and not current_user.is_superuser:
                    raise ValueError(f"Attribute {attribute.id} requires superuser privileges to remove")
                
                # Delete user attribute
                deleted_user_attribute = await user_attribute_service.delete_user_attribute(db, id=user_attribute_id)
                results.append(BatchResponseItem(
                    success=True,
                    data=deleted_user_attribute,
                    index=index
                ))
                success_count += 1
                
            else:
                raise ValueError(f"Unknown operation type: {operation.operation}")
                
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