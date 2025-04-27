from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from usery.models.refresh_token import RefreshToken
from usery.api.schemas.refresh_token import RefreshTokenCreate, RefreshTokenUpdate


async def get_refresh_token(db: AsyncSession, token: str) -> Optional[RefreshToken]:
    """Get a refresh token by token value."""
    result = await db.execute(select(RefreshToken).filter(RefreshToken.token == token))
    return result.scalars().first()


async def get_refresh_token_by_id(db: AsyncSession, token_id: UUID) -> Optional[RefreshToken]:
    """Get a refresh token by ID."""
    result = await db.execute(select(RefreshToken).filter(RefreshToken.id == token_id))
    return result.scalars().first()


async def get_valid_refresh_token(db: AsyncSession, token: str) -> Optional[RefreshToken]:
    """Get a valid (not expired, not revoked) refresh token by token value."""
    result = await db.execute(
        select(RefreshToken).filter(
            and_(
                RefreshToken.token == token,
                RefreshToken.expires_at > datetime.utcnow(),
                RefreshToken.revoked == False
            )
        )
    )
    return result.scalars().first()


async def get_user_refresh_tokens(
    db: AsyncSession, 
    user_id: UUID, 
    client_id: Optional[UUID] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[RefreshToken]:
    """Get refresh tokens for a user, optionally filtered by client."""
    query = select(RefreshToken).filter(RefreshToken.user_id == user_id)
    
    if client_id:
        query = query.filter(RefreshToken.client_id == client_id)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def create_refresh_token(
    db: AsyncSession, 
    token_in: RefreshTokenCreate,
    expires_in: Optional[int] = None  # If None, use the value from token_in.expires_at
) -> RefreshToken:
    """Create a new refresh token."""
    # Set expiration time if not provided in token_in but expires_in is provided
    if expires_in is not None and (not hasattr(token_in, 'expires_at') or token_in.expires_at is None):
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        token_in_dict = token_in.model_dump()
        token_in_dict['expires_at'] = expires_at
    else:
        token_in_dict = token_in.model_dump()
    
    db_token = RefreshToken(**token_in_dict)
    db.add(db_token)
    await db.commit()
    await db.refresh(db_token)
    return db_token


async def update_refresh_token(
    db: AsyncSession, 
    token: str, 
    token_in: RefreshTokenUpdate
) -> Optional[RefreshToken]:
    """Update a refresh token."""
    db_token = await get_refresh_token(db, token=token)
    if not db_token:
        return None
    
    update_data = token_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_token, field, value)
    
    await db.commit()
    await db.refresh(db_token)
    return db_token


async def revoke_refresh_token(db: AsyncSession, token: str) -> Optional[RefreshToken]:
    """Revoke a refresh token."""
    return await update_refresh_token(db, token, RefreshTokenUpdate(revoked=True))


async def revoke_user_tokens(
    db: AsyncSession, 
    user_id: UUID, 
    client_id: Optional[UUID] = None
) -> int:
    """Revoke all refresh tokens for a user, optionally filtered by client."""
    tokens = await get_user_refresh_tokens(db, user_id, client_id)
    
    count = 0
    for token in tokens:
        if not token.revoked:
            token.revoked = True
            count += 1
    
    await db.commit()
    return count


async def delete_refresh_token(db: AsyncSession, token_id: UUID) -> Optional[RefreshToken]:
    """Delete a refresh token."""
    db_token = await get_refresh_token_by_id(db, token_id=token_id)
    if not db_token:
        return None
    
    await db.delete(db_token)
    await db.commit()
    return db_token


async def clean_expired_tokens(db: AsyncSession) -> int:
    """Delete all expired refresh tokens."""
    result = await db.execute(
        select(RefreshToken).filter(RefreshToken.expires_at < datetime.utcnow())
    )
    expired_tokens = result.scalars().all()
    
    count = 0
    for token in expired_tokens:
        await db.delete(token)
        count += 1
    
    await db.commit()
    return count