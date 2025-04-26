from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from usery.models.user_attribute import UserAttribute
from usery.api.schemas.user_attribute import UserAttributeCreate, UserAttributeUpdate


async def get_user_attribute(db: AsyncSession, id: UUID) -> Optional[UserAttribute]:
    """Get a user attribute by id."""
    result = await db.execute(select(UserAttribute).filter(UserAttribute.id == id))
    return result.scalars().first()


async def get_user_attribute_by_user_and_attribute(
    db: AsyncSession, user_id: UUID, attribute_id: UUID
) -> Optional[UserAttribute]:
    """Get a user attribute by user_id and attribute_id."""
    result = await db.execute(
        select(UserAttribute).filter(
            UserAttribute.user_id == user_id,
            UserAttribute.attribute_id == attribute_id
        )
    )
    return result.scalars().first()


async def get_user_attributes(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[UserAttribute]:
    """Get a list of user attributes."""
    result = await db.execute(select(UserAttribute).offset(skip).limit(limit))
    return result.scalars().all()


async def get_user_attributes_by_user(
    db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 100
) -> List[UserAttribute]:
    """Get a list of user attributes by user_id."""
    result = await db.execute(
        select(UserAttribute)
        .filter(UserAttribute.user_id == user_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def get_user_attributes_by_attribute(
    db: AsyncSession, attribute_id: UUID, skip: int = 0, limit: int = 100
) -> List[UserAttribute]:
    """Get a list of user attributes by attribute_id."""
    result = await db.execute(
        select(UserAttribute)
        .filter(UserAttribute.attribute_id == attribute_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def create_user_attribute(
    db: AsyncSession, user_attribute_in: UserAttributeCreate
) -> UserAttribute:
    """Create a new user attribute."""
    db_user_attribute = UserAttribute(
        user_id=user_attribute_in.user_id,
        attribute_id=user_attribute_in.attribute_id,
        value=user_attribute_in.value,
    )
    db.add(db_user_attribute)
    await db.commit()
    await db.refresh(db_user_attribute)
    return db_user_attribute


async def update_user_attribute(
    db: AsyncSession, id: UUID, user_attribute_in: UserAttributeUpdate
) -> Optional[UserAttribute]:
    """Update a user attribute."""
    db_user_attribute = await get_user_attribute(db, id)
    if not db_user_attribute:
        return None
    
    update_data = user_attribute_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_user_attribute, field, value)
    
    db.add(db_user_attribute)
    await db.commit()
    await db.refresh(db_user_attribute)
    return db_user_attribute


async def delete_user_attribute(db: AsyncSession, id: UUID) -> Optional[UserAttribute]:
    """Delete a user attribute."""
    db_user_attribute = await get_user_attribute(db, id)
    if not db_user_attribute:
        return None
    
    await db.delete(db_user_attribute)
    await db.commit()
    return db_user_attribute