from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from usery.api.deps import get_current_superuser
from usery.api.schemas.key_pair import KeyPair, KeyPairCreate, KeyPairUpdate
from usery.api.schemas.batch import BatchRequest, BatchResponse, BatchResponseItem, BatchOperationType
from usery.db.session import get_db
from usery.models.user import User as UserModel
from usery.services.key_pair import (
    create_key_pair,
    delete_key_pair,
    get_key_pair,
    get_key_pairs,
    update_key_pair,
)

router = APIRouter()


@router.get("/", response_model=List[KeyPair])
async def read_key_pairs(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_superuser),
) -> Any:
    """
    Retrieve key pairs.
    
    Only superusers can access this endpoint.
    """
    key_pairs = await get_key_pairs(db, skip=skip, limit=limit)
    return key_pairs


@router.post("/", response_model=KeyPair, status_code=status.HTTP_201_CREATED)
async def create_new_key_pair(
    *,
    db: AsyncSession = Depends(get_db),
    key_pair_in: KeyPairCreate,
    current_user: UserModel = Depends(get_current_superuser),
) -> Any:
    """
    Create new key pair.
    
    Only superusers can create key pairs.
    """
    key_pair = await create_key_pair(db, key_pair_in=key_pair_in)
    return key_pair


@router.get("/{key_pair_id}", response_model=KeyPair)
async def read_key_pair(
    *,
    db: AsyncSession = Depends(get_db),
    key_pair_id: UUID,
    current_user: UserModel = Depends(get_current_superuser),
) -> Any:
    """
    Get a specific key pair by id.
    
    Only superusers can access this endpoint.
    """
    key_pair = await get_key_pair(db, key_pair_id=key_pair_id)
    if not key_pair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Key pair not found",
        )
    
    return key_pair


@router.put("/{key_pair_id}", response_model=KeyPair)
async def update_key_pair_info(
    *,
    db: AsyncSession = Depends(get_db),
    key_pair_id: UUID,
    key_pair_in: KeyPairUpdate,
    current_user: UserModel = Depends(get_current_superuser),
) -> Any:
    """
    Update a key pair.
    
    Only superusers can update key pairs.
    """
    key_pair = await get_key_pair(db, key_pair_id=key_pair_id)
    if not key_pair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Key pair not found",
        )
    
    key_pair = await update_key_pair(db, key_pair_id=key_pair_id, key_pair_in=key_pair_in)
    return key_pair


@router.delete("/{key_pair_id}", response_model=KeyPair)
async def delete_key_pair_by_id(
    *,
    db: AsyncSession = Depends(get_db),
    key_pair_id: UUID,
    current_user: UserModel = Depends(get_current_superuser),
) -> Any:
    """
    Delete a key pair.
    
    Only superusers can delete key pairs.
    """
    key_pair = await get_key_pair(db, key_pair_id=key_pair_id)
    if not key_pair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Key pair not found",
        )
    
    key_pair = await delete_key_pair(db, key_pair_id=key_pair_id)
    return key_pair


@router.post("/batch", response_model=BatchResponse)
async def batch_key_pairs_operations(
    *,
    db: AsyncSession = Depends(get_db),
    batch_request: BatchRequest[KeyPairCreate | KeyPairUpdate],
    current_user: UserModel = Depends(get_current_superuser),
) -> Any:
    """
    Perform batch operations on key pairs (create, update, delete).
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
                
                key_pair_data = operation.data
                key_pair = await create_key_pair(db, key_pair_in=key_pair_data)
                results.append(BatchResponseItem(
                    success=True,
                    data=key_pair,
                    index=index
                ))
                success_count += 1
                
            elif operation.operation == BatchOperationType.UPDATE:
                if not operation.id:
                    raise ValueError("ID is required for update operation")
                if not operation.data:
                    raise ValueError("Data is required for update operation")
                
                key_pair_id = operation.id
                key_pair_data = operation.data
                
                # Check if key pair exists
                key_pair = await get_key_pair(db, key_pair_id=key_pair_id)
                if not key_pair:
                    raise ValueError(f"Key pair with ID {key_pair_id} not found")
                
                updated_key_pair = await update_key_pair(db, key_pair_id=key_pair_id, key_pair_in=key_pair_data)
                results.append(BatchResponseItem(
                    success=True,
                    data=updated_key_pair,
                    index=index
                ))
                success_count += 1
                
            elif operation.operation == BatchOperationType.DELETE:
                if not operation.id:
                    raise ValueError("ID is required for delete operation")
                
                key_pair_id = operation.id
                
                # Check if key pair exists
                key_pair = await get_key_pair(db, key_pair_id=key_pair_id)
                if not key_pair:
                    raise ValueError(f"Key pair with ID {key_pair_id} not found")
                
                deleted_key_pair = await delete_key_pair(db, key_pair_id=key_pair_id)
                results.append(BatchResponseItem(
                    success=True,
                    data=deleted_key_pair,
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