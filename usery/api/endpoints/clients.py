from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from usery.api.deps import get_current_superuser
from usery.api.schemas.client import Client, ClientCreate, ClientUpdate
from usery.api.schemas.batch import BatchRequest, BatchResponse, BatchResponseItem, BatchOperationType
from usery.db.session import get_db
from usery.models.user import User as UserModel
from usery.services.client import (
    create_client,
    delete_client,
    get_client,
    get_clients,
    update_client,
)

router = APIRouter()


@router.get("/", response_model=List[Client])
async def read_clients(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_superuser),
) -> Any:
    """
    Retrieve clients.
    
    Only superusers can list clients.
    """
    clients = await get_clients(db, skip=skip, limit=limit)
    return clients


@router.post("/", response_model=Client, status_code=status.HTTP_201_CREATED)
async def create_new_client(
    *,
    db: AsyncSession = Depends(get_db),
    client_in: ClientCreate,
    current_user: UserModel = Depends(get_current_superuser),
) -> Any:
    """
    Create new client.
    
    Only superusers can create clients.
    """
    client = await create_client(db, client_in=client_in)
    return client


@router.get("/{client_id}", response_model=Client)
async def read_client(
    *,
    db: AsyncSession = Depends(get_db),
    client_id: UUID,
    current_user: UserModel = Depends(get_current_superuser),
) -> Any:
    """
    Get a specific client by id.
    
    Only superusers can view clients.
    """
    client = await get_client(db, client_id=client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    
    return client


@router.put("/{client_id}", response_model=Client)
async def update_client_info(
    *,
    db: AsyncSession = Depends(get_db),
    client_id: UUID,
    client_in: ClientUpdate,
    current_user: UserModel = Depends(get_current_superuser),
) -> Any:
    """
    Update a client.
    
    Only superusers can update clients.
    """
    client = await get_client(db, client_id=client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    
    client = await update_client(db, client_id=client_id, client_in=client_in)
    return client


@router.delete("/{client_id}", response_model=Client)
async def delete_client_by_id(
    *,
    db: AsyncSession = Depends(get_db),
    client_id: UUID,
    current_user: UserModel = Depends(get_current_superuser),
) -> Any:
    """
    Delete a client.
    
    Only superusers can delete clients.
    """
    client = await get_client(db, client_id=client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    
    client = await delete_client(db, client_id=client_id)
    return client


@router.post("/batch", response_model=BatchResponse)
async def batch_clients_operations(
    *,
    db: AsyncSession = Depends(get_db),
    batch_request: BatchRequest[ClientCreate | ClientUpdate],
    current_user: UserModel = Depends(get_current_superuser),
) -> Any:
    """
    Perform batch operations on clients (create, update, delete).
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
                
                client_data = operation.data
                client = await create_client(db, client_in=client_data)
                results.append(BatchResponseItem(
                    success=True,
                    data=client,
                    index=index
                ))
                success_count += 1
                
            elif operation.operation == BatchOperationType.UPDATE:
                if not operation.id:
                    raise ValueError("ID is required for update operation")
                if not operation.data:
                    raise ValueError("Data is required for update operation")
                
                client_id = operation.id
                client_data = operation.data
                
                # Check if client exists
                client = await get_client(db, client_id=client_id)
                if not client:
                    raise ValueError(f"Client with ID {client_id} not found")
                
                updated_client = await update_client(db, client_id=client_id, client_in=client_data)
                results.append(BatchResponseItem(
                    success=True,
                    data=updated_client,
                    index=index
                ))
                success_count += 1
                
            elif operation.operation == BatchOperationType.DELETE:
                if not operation.id:
                    raise ValueError("ID is required for delete operation")
                
                client_id = operation.id
                
                # Check if client exists
                client = await get_client(db, client_id=client_id)
                if not client:
                    raise ValueError(f"Client with ID {client_id} not found")
                
                deleted_client = await delete_client(db, client_id=client_id)
                results.append(BatchResponseItem(
                    success=True,
                    data=deleted_client,
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