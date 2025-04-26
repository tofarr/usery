from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from usery.models.user_tag import UserTag
from usery.models.user import User
from usery.models.tag import Tag
from usery.api.schemas.user_tag import UserTagCreate


async def get_user_tag(db: AsyncSession, user_id: UUID, tag_code: str) -> Optional[UserTag]:
    """Get a user tag by user_id and tag_code."""
    result = await db.execute(
        select(UserTag).filter(
            UserTag.user_id == user_id,
            UserTag.tag_code == tag_code
        )
    )
    return result.scalars().first()


async def get_user_tags(db: AsyncSession, user_id: UUID) -> List[UserTag]:
    """Get all tags for a user."""
    result = await db.execute(
        select(UserTag).filter(UserTag.user_id == user_id)
    )
    return result.scalars().all()


async def get_tag_users(db: AsyncSession, tag_code: str) -> List[UserTag]:
    """Get all users for a tag."""
    result = await db.execute(
        select(UserTag).filter(UserTag.tag_code == tag_code)
    )
    return result.scalars().all()


async def get_user_tags_with_details(db: AsyncSession, user_id: UUID) -> List[dict]:
    """Get all tags for a user with tag details."""
    query = (
        select(UserTag, Tag)
        .join(Tag, UserTag.tag_code == Tag.code)
        .filter(UserTag.user_id == user_id)
    )
    result = await db.execute(query)
    return [{"user_tag": user_tag, "tag": tag} for user_tag, tag in result]


async def get_tag_users_with_details(db: AsyncSession, tag_code: str) -> List[dict]:
    """Get all users for a tag with user details."""
    query = (
        select(UserTag, User)
        .join(User, UserTag.user_id == User.id)
        .filter(UserTag.tag_code == tag_code)
    )
    result = await db.execute(query)
    return [{"user_tag": user_tag, "user": user} for user_tag, user in result]


async def create_user_tag(db: AsyncSession, user_tag_in: UserTagCreate) -> UserTag:
    """Create a new user tag."""
    db_user_tag = UserTag(
        user_id=user_tag_in.user_id,
        tag_code=user_tag_in.tag_code,
    )
    db.add(db_user_tag)
    await db.commit()
    await db.refresh(db_user_tag)
    return db_user_tag


async def delete_user_tag(db: AsyncSession, user_id: UUID, tag_code: str) -> Optional[UserTag]:
    """Delete a user tag."""
    db_user_tag = await get_user_tag(db, user_id, tag_code)
    if not db_user_tag:
        return None
    
    await db.delete(db_user_tag)
    await db.commit()
    return db_user_tag