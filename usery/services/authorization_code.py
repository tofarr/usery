from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from usery.models.authorization_code import AuthorizationCode
from usery.api.schemas.authorization_code import AuthorizationCodeCreate, AuthorizationCodeUpdate


async def get_authorization_code(db: AsyncSession, code: str) -> Optional[AuthorizationCode]:
    """Get an authorization code by code value."""
    result = await db.execute(select(AuthorizationCode).filter(AuthorizationCode.code == code))
    return result.scalars().first()


async def get_authorization_code_by_id(db: AsyncSession, code_id: UUID) -> Optional[AuthorizationCode]:
    """Get an authorization code by ID."""
    result = await db.execute(select(AuthorizationCode).filter(AuthorizationCode.id == code_id))
    return result.scalars().first()


async def get_valid_authorization_code(db: AsyncSession, code: str) -> Optional[AuthorizationCode]:
    """Get a valid (not expired, not used) authorization code by code value."""
    result = await db.execute(
        select(AuthorizationCode).filter(
            and_(
                AuthorizationCode.code == code,
                AuthorizationCode.expires_at > datetime.utcnow(),
                AuthorizationCode.used == False
            )
        )
    )
    return result.scalars().first()


async def create_authorization_code(
    db: AsyncSession, 
    code_in: AuthorizationCodeCreate,
    expires_in: int = 600  # Default 10 minutes
) -> AuthorizationCode:
    """Create a new authorization code."""
    # Set expiration time if not provided
    if not hasattr(code_in, 'expires_at') or code_in.expires_at is None:
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        code_in_dict = code_in.model_dump()
        code_in_dict['expires_at'] = expires_at
    else:
        code_in_dict = code_in.model_dump()
    
    db_code = AuthorizationCode(**code_in_dict)
    db.add(db_code)
    await db.commit()
    await db.refresh(db_code)
    return db_code


async def update_authorization_code(
    db: AsyncSession, 
    code: str, 
    code_in: AuthorizationCodeUpdate
) -> Optional[AuthorizationCode]:
    """Update an authorization code."""
    db_code = await get_authorization_code(db, code=code)
    if not db_code:
        return None
    
    update_data = code_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_code, field, value)
    
    await db.commit()
    await db.refresh(db_code)
    return db_code


async def mark_code_as_used(db: AsyncSession, code: str) -> Optional[AuthorizationCode]:
    """Mark an authorization code as used."""
    return await update_authorization_code(db, code, AuthorizationCodeUpdate(used=True))


async def delete_authorization_code(db: AsyncSession, code_id: UUID) -> Optional[AuthorizationCode]:
    """Delete an authorization code."""
    db_code = await get_authorization_code_by_id(db, code_id=code_id)
    if not db_code:
        return None
    
    await db.delete(db_code)
    await db.commit()
    return db_code


async def clean_expired_codes(db: AsyncSession) -> int:
    """Delete all expired authorization codes."""
    result = await db.execute(
        select(AuthorizationCode).filter(AuthorizationCode.expires_at < datetime.utcnow())
    )
    expired_codes = result.scalars().all()
    
    count = 0
    for code in expired_codes:
        await db.delete(code)
        count += 1
    
    await db.commit()
    return count