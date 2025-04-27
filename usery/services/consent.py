from typing import List, Optional, Set
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from usery.models.consent import Consent
from usery.api.schemas.consent import ConsentCreate, ConsentUpdate


async def get_consent(db: AsyncSession, consent_id: UUID) -> Optional[Consent]:
    """Get a consent record by ID."""
    result = await db.execute(select(Consent).filter(Consent.id == consent_id))
    return result.scalars().first()


async def get_active_consent(db: AsyncSession, user_id: UUID, client_id: UUID) -> Optional[Consent]:
    """Get the active consent record for a user-client pair."""
    result = await db.execute(
        select(Consent).filter(
            and_(
                Consent.user_id == user_id,
                Consent.client_id == client_id,
                Consent.is_active == True
            )
        )
    )
    return result.scalars().first()


async def get_user_consents(
    db: AsyncSession, 
    user_id: UUID, 
    active_only: bool = True,
    skip: int = 0, 
    limit: int = 100
) -> List[Consent]:
    """Get consent records for a user."""
    query = select(Consent).filter(Consent.user_id == user_id)
    
    if active_only:
        query = query.filter(Consent.is_active == True)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def create_consent(db: AsyncSession, consent_in: ConsentCreate) -> Consent:
    """Create a new consent record."""
    # First, deactivate any existing active consent for this user-client pair
    existing_consent = await get_active_consent(
        db, 
        user_id=consent_in.user_id, 
        client_id=consent_in.client_id
    )
    
    if existing_consent:
        existing_consent.is_active = False
        db.add(existing_consent)
    
    # Create new consent record
    db_consent = Consent(**consent_in.model_dump())
    db.add(db_consent)
    await db.commit()
    await db.refresh(db_consent)
    return db_consent


async def update_consent(
    db: AsyncSession, 
    consent_id: UUID, 
    consent_in: ConsentUpdate
) -> Optional[Consent]:
    """Update a consent record."""
    db_consent = await get_consent(db, consent_id=consent_id)
    if not db_consent:
        return None
    
    update_data = consent_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_consent, field, value)
    
    await db.commit()
    await db.refresh(db_consent)
    return db_consent


async def deactivate_consent(db: AsyncSession, consent_id: UUID) -> Optional[Consent]:
    """Deactivate a consent record."""
    return await update_consent(db, consent_id, ConsentUpdate(is_active=False))


async def has_user_consented_to_scopes(
    db: AsyncSession, 
    user_id: UUID, 
    client_id: UUID, 
    required_scopes: List[str]
) -> bool:
    """Check if a user has consented to all the required scopes for a client."""
    consent = await get_active_consent(db, user_id, client_id)
    if not consent:
        return False
    
    # Convert to sets for easier comparison
    required_scope_set = set(required_scopes)
    consented_scope_set = set(consent.scopes)
    
    # Check if all required scopes are in the consented scopes
    return required_scope_set.issubset(consented_scope_set)


async def get_consented_scopes(
    db: AsyncSession, 
    user_id: UUID, 
    client_id: UUID
) -> Set[str]:
    """Get the set of scopes a user has consented to for a client."""
    consent = await get_active_consent(db, user_id, client_id)
    if not consent:
        return set()
    
    return set(consent.scopes)


async def delete_consent(db: AsyncSession, consent_id: UUID) -> Optional[Consent]:
    """Delete a consent record."""
    db_consent = await get_consent(db, consent_id=consent_id)
    if not db_consent:
        return None
    
    await db.delete(db_consent)
    await db.commit()
    return db_consent