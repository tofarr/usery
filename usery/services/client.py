from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from usery.models.client import Client
from usery.api.schemas.client import ClientCreate, ClientUpdate


async def get_client(db: AsyncSession, client_id: UUID) -> Optional[Client]:
    """Get a client by ID."""
    result = await db.execute(select(Client).filter(Client.id == client_id))
    return result.scalars().first()


async def get_clients(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Client]:
    """Get a list of clients."""
    result = await db.execute(select(Client).offset(skip).limit(limit))
    return result.scalars().all()


async def create_client(db: AsyncSession, client_in: ClientCreate) -> Client:
    """Create a new client."""
    db_client = Client(
        title=client_in.title,
        description=client_in.description,
        access_token_timeout=client_in.access_token_timeout,
        refresh_token_timeout=client_in.refresh_token_timeout,
    )
    db.add(db_client)
    await db.commit()
    await db.refresh(db_client)
    return db_client


async def update_client(db: AsyncSession, client_id: UUID, client_in: ClientUpdate) -> Optional[Client]:
    """Update a client."""
    db_client = await get_client(db, client_id)
    if not db_client:
        return None
    
    update_data = client_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_client, field, value)
    
    db.add(db_client)
    await db.commit()
    await db.refresh(db_client)
    return db_client


async def delete_client(db: AsyncSession, client_id: UUID) -> Optional[Client]:
    """Delete a client."""
    db_client = await get_client(db, client_id)
    if not db_client:
        return None
    
    await db.delete(db_client)
    await db.commit()
    return db_client