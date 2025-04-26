from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from usery.models.tag import Tag
from usery.models.user_tag import UserTag
from usery.api.schemas.tag import TagCreate, TagUpdate


async def get_tag(db: AsyncSession, code: str) -> Optional[Tag]:
    """Get a tag by code."""
    result = await db.execute(select(Tag).filter(Tag.code == code))
    return result.scalars().first()


async def get_tags(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Tag]:
    """Get a list of tags."""
    result = await db.execute(select(Tag).offset(skip).limit(limit))
    return result.scalars().all()


async def get_tag_with_user_count(db: AsyncSession, code: str) -> Optional[dict]:
    """Get a tag with user count."""
    query = (
        select(Tag, func.count(UserTag.user_id).label("user_count"))
        .outerjoin(UserTag, Tag.code == UserTag.tag_code)
        .filter(Tag.code == code)
        .group_by(Tag.code)
    )
    result = await db.execute(query)
    row = result.first()
    if not row:
        return None
    
    tag, user_count = row
    return {"tag": tag, "user_count": user_count}


async def get_tags_with_user_count(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[dict]:
    """Get a list of tags with user count."""
    query = (
        select(Tag, func.count(UserTag.user_id).label("user_count"))
        .outerjoin(UserTag, Tag.code == UserTag.tag_code)
        .group_by(Tag.code)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return [{"tag": tag, "user_count": user_count} for tag, user_count in result]


async def create_tag(db: AsyncSession, tag_in: TagCreate) -> Tag:
    """Create a new tag."""
    db_tag = Tag(
        code=tag_in.code,
        title=tag_in.title,
        description=tag_in.description,
    )
    db.add(db_tag)
    await db.commit()
    await db.refresh(db_tag)
    return db_tag


async def update_tag(db: AsyncSession, code: str, tag_in: TagUpdate) -> Optional[Tag]:
    """Update a tag."""
    db_tag = await get_tag(db, code)
    if not db_tag:
        return None
    
    update_data = tag_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_tag, field, value)
    
    db.add(db_tag)
    await db.commit()
    await db.refresh(db_tag)
    return db_tag


async def delete_tag(db: AsyncSession, code: str) -> Optional[Tag]:
    """Delete a tag."""
    db_tag = await get_tag(db, code)
    if not db_tag:
        return None
    
    await db.delete(db_tag)
    await db.commit()
    return db_tag