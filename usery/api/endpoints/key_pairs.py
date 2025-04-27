from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from usery.api.schemas.key_pair import KeyPair, KeyPairCreate, KeyPairUpdate
from usery.services import key_pair as key_pair_service
from usery.api.deps import get_db, get_current_superuser


router = APIRouter()


@router.get("/", response_model=List[KeyPair])
async def read_key_pairs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_superuser),
) -> List[KeyPair]:
    """
    Retrieve key pairs.
    
    Only superusers can access this endpoint.
    """
    key_pairs = await key_pair_service.get_key_pairs(db, skip=skip, limit=limit)
    return key_pairs


@router.post("/", response_model=KeyPair, status_code=status.HTTP_201_CREATED)
async def create_key_pair(
    key_pair_in: KeyPairCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_superuser),
) -> KeyPair:
    """
    Create new key pair.
    
    Only superusers can access this endpoint.
    """
    key_pair = await key_pair_service.create_key_pair(db, key_pair_in)
    return key_pair


@router.get("/{id}", response_model=KeyPair)
async def read_key_pair(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_superuser),
) -> KeyPair:
    """
    Get key pair by ID.
    
    Only superusers can access this endpoint.
    """
    key_pair = await key_pair_service.get_key_pair(db, id)
    if not key_pair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Key pair not found",
        )
    return key_pair


@router.put("/{id}", response_model=KeyPair)
async def update_key_pair(
    id: UUID,
    key_pair_in: KeyPairUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_superuser),
) -> KeyPair:
    """
    Update a key pair.
    
    Only superusers can access this endpoint.
    """
    key_pair = await key_pair_service.update_key_pair(db, id, key_pair_in)
    if not key_pair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Key pair not found",
        )
    return key_pair


@router.delete("/{id}", response_model=KeyPair)
async def delete_key_pair(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_superuser),
) -> KeyPair:
    """
    Delete a key pair.
    
    Only superusers can access this endpoint.
    """
    key_pair = await key_pair_service.delete_key_pair(db, id)
    if not key_pair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Key pair not found",
        )
    return key_pair