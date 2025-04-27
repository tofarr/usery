from typing import List, Optional, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from usery.api.deps import get_current_user, get_db, get_current_superuser
from usery.api.schemas.attribute import Attribute, AttributeCreate, AttributeUpdate, AttributeWithUserCount
from usery.api.schemas.user import User
from usery.api.schemas.batch import BatchRequest, BatchResponse, BatchResponseItem, BatchOperationType
from usery.services import attribute as attribute_service
from usery.services import user as user_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=List[Attribute])
async def read_attributes(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve attributes.
    """
    attributes = await attribute_service.get_attributes(db, skip=skip, limit=limit)
    return attributes


@router.get("/with-user-count", response_model=List[AttributeWithUserCount])
async def read_attributes_with_user_count(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve attributes with user count.
    """
    attributes_with_count = await attribute_service.get_attributes_with_user_count(db, skip=skip, limit=limit)
    return [
        AttributeWithUserCount(
            id=item["attribute"].id,
            json_schema=item["attribute"].schema,  # Map schema from DB to json_schema in API
            created_at=item["attribute"].created_at,
            updated_at=item["attribute"].updated_at,
            user_count=item["user_count"]
        )
        for item in attributes_with_count
    ]


@router.post("/", response_model=Attribute)
async def create_attribute(
    attribute_in: AttributeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create new attribute.
    """
    # Check if current user is superuser
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create attributes",
        )
    
    return await attribute_service.create_attribute(db, attribute_in=attribute_in)


@router.get("/{id}", response_model=Attribute)
async def read_attribute(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get attribute by id.
    """
    attribute = await attribute_service.get_attribute(db, id=id)
    if not attribute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attribute not found",
        )
    return attribute


@router.get("/{id}/with-user-count", response_model=AttributeWithUserCount)
async def read_attribute_with_user_count(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get attribute by id with user count.
    """
    attribute_with_count = await attribute_service.get_attribute_with_user_count(db, id=id)
    if not attribute_with_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attribute not found",
        )
    
    return AttributeWithUserCount(
        id=attribute_with_count["attribute"].id,
        json_schema=attribute_with_count["attribute"].schema,  # Map schema from DB to json_schema in API
        created_at=attribute_with_count["attribute"].created_at,
        updated_at=attribute_with_count["attribute"].updated_at,
        user_count=attribute_with_count["user_count"]
    )


@router.put("/{id}", response_model=Attribute)
async def update_attribute(
    id: UUID,
    attribute_in: AttributeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an attribute.
    """
    # Check if current user is superuser
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update attributes",
        )
    
    attribute = await attribute_service.get_attribute(db, id=id)
    if not attribute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attribute not found",
        )
    
    attribute = await attribute_service.update_attribute(db, id=id, attribute_in=attribute_in)
    return attribute


@router.delete("/{id}", response_model=Attribute)
async def delete_attribute(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete an attribute.
    """
    # Check if current user is superuser
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete attributes",
        )
    
    attribute = await attribute_service.delete_attribute(db, id=id)
    if not attribute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attribute not found",
        )
    
    return attribute


@router.post("/batch", response_model=BatchResponse)
async def batch_attributes_operations(
    *,
    db: AsyncSession = Depends(get_db),
    batch_request: BatchRequest[AttributeCreate | AttributeUpdate],
    current_user: User = Depends(get_current_superuser),
) -> Any:
    """
    Perform batch operations on attributes (create, update, delete).
    Only superusers can perform batch operations.
    """
    results = []
    success_count = 0
    error_count = 0

    for index, operation in enumerate(batch_request.operations):
        try:
            if operation.operation == BatchOperationType.CREATE:
                if not operation.data:
                    raise ValueError("Data is required for create operation")
                
                attribute_data = operation.data
                attribute = await attribute_service.create_attribute(db, attribute_in=attribute_data)
                results.append(BatchResponseItem(
                    success=True,
                    data=attribute,
                    index=index
                ))
                success_count += 1
                
            elif operation.operation == BatchOperationType.UPDATE:
                if not operation.id:
                    raise ValueError("ID is required for update operation")
                if not operation.data:
                    raise ValueError("Data is required for update operation")
                
                attribute_id = operation.id
                attribute_data = operation.data
                
                # Check if attribute exists
                attribute = await attribute_service.get_attribute(db, id=attribute_id)
                if not attribute:
                    raise ValueError(f"Attribute with ID {attribute_id} not found")
                
                updated_attribute = await attribute_service.update_attribute(
                    db, id=attribute_id, attribute_in=attribute_data
                )
                results.append(BatchResponseItem(
                    success=True,
                    data=updated_attribute,
                    index=index
                ))
                success_count += 1
                
            elif operation.operation == BatchOperationType.DELETE:
                if not operation.id:
                    raise ValueError("ID is required for delete operation")
                
                attribute_id = operation.id
                
                # Check if attribute exists
                attribute = await attribute_service.get_attribute(db, id=attribute_id)
                if not attribute:
                    raise ValueError(f"Attribute with ID {attribute_id} not found")
                
                deleted_attribute = await attribute_service.delete_attribute(db, id=attribute_id)
                results.append(BatchResponseItem(
                    success=True,
                    data=deleted_attribute,
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