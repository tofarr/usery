from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from usery.models.key_pair import KeyPair
from usery.api.schemas.key_pair import KeyPairCreate, KeyPairUpdate


async def get_key_pair(db: AsyncSession, key_pair_id: UUID) -> Optional[KeyPair]:
    """Get a key pair by ID."""
    result = await db.execute(select(KeyPair).filter(KeyPair.id == key_pair_id))
    return result.scalars().first()


async def get_key_pairs(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[KeyPair]:
    """Get a list of key pairs."""
    result = await db.execute(select(KeyPair).offset(skip).limit(limit))
    return result.scalars().all()


async def get_active_key_pairs(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[KeyPair]:
    """Get a list of active key pairs."""
    result = await db.execute(select(KeyPair).filter(KeyPair.is_active == True).offset(skip).limit(limit))
    return result.scalars().all()


async def create_key_pair(db: AsyncSession, key_pair_in: KeyPairCreate) -> KeyPair:
    """Create a new key pair."""
    db_key_pair = KeyPair(
        algorithm=key_pair_in.algorithm,
        public_key=key_pair_in.public_key,
        private_key=key_pair_in.private_key,
        is_active=key_pair_in.is_active,
    )
    db.add(db_key_pair)
    await db.commit()
    await db.refresh(db_key_pair)
    return db_key_pair


async def update_key_pair(db: AsyncSession, key_pair_id: UUID, key_pair_in: KeyPairUpdate) -> Optional[KeyPair]:
    """Update a key pair."""
    db_key_pair = await get_key_pair(db, key_pair_id=key_pair_id)
    if not db_key_pair:
        return None
    
    update_data = key_pair_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_key_pair, field, value)
    
    await db.commit()
    await db.refresh(db_key_pair)
    return db_key_pair


async def delete_key_pair(db: AsyncSession, key_pair_id: UUID) -> Optional[KeyPair]:
    """Delete a key pair."""
    db_key_pair = await get_key_pair(db, key_pair_id=key_pair_id)
    if not db_key_pair:
        return None
    
    await db.delete(db_key_pair)
    await db.commit()
    return db_key_pair