from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from usery.models.key_pair import KeyPair
from usery.api.schemas.key_pair import KeyPairCreate, KeyPairUpdate


def generate_key_pair() -> tuple[str, str]:
    """Generate a new RSA key pair."""
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Get private key in PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    # Get public key in PEM format
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    return public_pem, private_pem


async def get_key_pair(db: AsyncSession, id: UUID) -> Optional[KeyPair]:
    """Get a key pair by id."""
    result = await db.execute(select(KeyPair).filter(KeyPair.id == id))
    return result.scalars().first()


async def get_active_key_pair(db: AsyncSession) -> Optional[KeyPair]:
    """Get the active key pair."""
    result = await db.execute(select(KeyPair).filter(KeyPair.active == True).order_by(KeyPair.created_at.desc()))
    return result.scalars().first()


async def get_key_pairs(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[KeyPair]:
    """Get a list of key pairs."""
    result = await db.execute(select(KeyPair).offset(skip).limit(limit))
    return result.scalars().all()


async def create_key_pair(db: AsyncSession, key_pair_in: KeyPairCreate) -> KeyPair:
    """Create a new key pair."""
    # Generate new RSA key pair
    public_key, private_key = generate_key_pair()
    
    # If this is the first key pair or it's set to active, deactivate all other key pairs
    if key_pair_in.active:
        await deactivate_all_key_pairs(db)
    
    # Create new key pair
    db_key_pair = KeyPair(
        public_key=public_key,
        private_key=private_key,
        active=key_pair_in.active,
    )
    db.add(db_key_pair)
    await db.commit()
    await db.refresh(db_key_pair)
    return db_key_pair


async def update_key_pair(db: AsyncSession, id: UUID, key_pair_in: KeyPairUpdate) -> Optional[KeyPair]:
    """Update a key pair."""
    db_key_pair = await get_key_pair(db, id)
    if not db_key_pair:
        return None
    
    update_data = key_pair_in.model_dump(exclude_unset=True)
    
    # If setting this key pair to active, deactivate all other key pairs
    if update_data.get("active", False):
        await deactivate_all_key_pairs(db)
    
    for field, value in update_data.items():
        setattr(db_key_pair, field, value)
    
    db.add(db_key_pair)
    await db.commit()
    await db.refresh(db_key_pair)
    return db_key_pair


async def delete_key_pair(db: AsyncSession, id: UUID) -> Optional[KeyPair]:
    """Delete a key pair."""
    db_key_pair = await get_key_pair(db, id)
    if not db_key_pair:
        return None
    
    await db.delete(db_key_pair)
    await db.commit()
    return db_key_pair


async def deactivate_all_key_pairs(db: AsyncSession) -> None:
    """Deactivate all key pairs."""
    key_pairs = await get_key_pairs(db)
    for key_pair in key_pairs:
        key_pair.active = False
        db.add(key_pair)
    
    await db.commit()