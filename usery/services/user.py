from typing import List, Optional, Dict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from uuid import UUID

from usery.models.user import User
from usery.models.user_tag import UserTag
from usery.api.schemas.user import UserCreate, UserUpdate
from usery.services.security import get_password_hash, verify_password


async def get_user(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """Get a user by ID."""
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get a user by email."""
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Get a user by username."""
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalars().first()


async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    """Get a list of users."""
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()


async def count_users(db: AsyncSession) -> int:
    """Count the total number of users in the system."""
    result = await db.execute(select(func.count()).select_from(User))
    return result.scalar_one()


async def get_user_with_tags(db: AsyncSession, user_id: UUID) -> Optional[Dict]:
    """Get a user with their tags."""
    db_user = await get_user(db, user_id)
    if not db_user:
        return None
    
    result = await db.execute(
        select(UserTag.tag_code).filter(UserTag.user_id == user_id)
    )
    tag_codes = result.scalars().all()
    
    return {"user": db_user, "tags": tag_codes}


async def get_users_by_tag(db: AsyncSession, tag_code: str, skip: int = 0, limit: int = 100) -> List[User]:
    """Get all users with a specific tag."""
    query = (
        select(User)
        .join(UserTag, User.id == UserTag.user_id)
        .filter(UserTag.tag_code == tag_code)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """Create a new user."""
    db_user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def update_user(db: AsyncSession, user_id: UUID, user_in: UserUpdate) -> Optional[User]:
    """Update a user."""
    db_user = await get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user_in.model_dump(exclude_unset=True)
    
    if "password" in update_data:
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        update_data["hashed_password"] = hashed_password
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def delete_user(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """Delete a user."""
    db_user = await get_user(db, user_id)
    if not db_user:
        return None
    
    await db.delete(db_user)
    await db.commit()
    return db_user


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    """Authenticate a user."""
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user