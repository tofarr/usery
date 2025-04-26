from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from usery.models.attribute import Attribute
from usery.models.user_attribute import UserAttribute
from usery.api.schemas.attribute import AttributeCreate, AttributeUpdate


async def get_attribute(db: AsyncSession, id: UUID) -> Optional[Attribute]:
    """Get an attribute by id."""
    result = await db.execute(select(Attribute).filter(Attribute.id == id))
    return result.scalars().first()


async def get_attributes(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Attribute]:
    """Get a list of attributes."""
    result = await db.execute(select(Attribute).offset(skip).limit(limit))
    return result.scalars().all()


async def get_attribute_with_user_count(db: AsyncSession, id: UUID) -> Optional[dict]:
    """Get an attribute with user count."""
    query = (
        select(Attribute, func.count(UserAttribute.user_id).label("user_count"))
        .outerjoin(UserAttribute, Attribute.id == UserAttribute.attribute_id)
        .filter(Attribute.id == id)
        .group_by(Attribute.id)
    )
    result = await db.execute(query)
    row = result.first()
    if not row:
        return None
    
    attribute, user_count = row
    return {"attribute": attribute, "user_count": user_count}


async def get_attributes_with_user_count(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[dict]:
    """Get a list of attributes with user count."""
    query = (
        select(Attribute, func.count(UserAttribute.user_id).label("user_count"))
        .outerjoin(UserAttribute, Attribute.id == UserAttribute.attribute_id)
        .group_by(Attribute.id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return [{"attribute": attribute, "user_count": user_count} for attribute, user_count in result]


async def create_attribute(db: AsyncSession, attribute_in: AttributeCreate) -> Attribute:
    """Create a new attribute."""
    db_attribute = Attribute(
        schema=attribute_in.json_schema,
    )
    db.add(db_attribute)
    await db.commit()
    await db.refresh(db_attribute)
    return db_attribute


async def update_attribute(db: AsyncSession, id: UUID, attribute_in: AttributeUpdate) -> Optional[Attribute]:
    """Update an attribute."""
    db_attribute = await get_attribute(db, id)
    if not db_attribute:
        return None
    
    update_data = attribute_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_attribute, field, value)
    
    db.add(db_attribute)
    await db.commit()
    await db.refresh(db_attribute)
    return db_attribute


async def delete_attribute(db: AsyncSession, id: UUID) -> Optional[Attribute]:
    """Delete an attribute."""
    db_attribute = await get_attribute(db, id)
    if not db_attribute:
        return None
    
    await db.delete(db_attribute)
    await db.commit()
    return db_attribute