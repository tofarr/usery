from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from usery.api.deps import get_current_user, get_db
from usery.api.schemas.tag import Tag, TagCreate, TagUpdate, TagWithUsers
from usery.api.schemas.user import User
from usery.services import tag as tag_service
from usery.services import user as user_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=List[Tag])
async def read_tags(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve tags.
    """
    tags = await tag_service.get_tags(db, skip=skip, limit=limit)
    return tags


@router.get("/with-user-count", response_model=List[TagWithUsers])
async def read_tags_with_user_count(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve tags with user count.
    """
    tags_with_count = await tag_service.get_tags_with_user_count(db, skip=skip, limit=limit)
    return [
        TagWithUsers(
            code=item["tag"].code,
            title=item["tag"].title,
            description=item["tag"].description,
            created_at=item["tag"].created_at,
            updated_at=item["tag"].updated_at,
            user_count=item["user_count"]
        )
        for item in tags_with_count
    ]


@router.post("/", response_model=Tag)
async def create_tag(
    tag_in: TagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create new tag.
    """
    # Check if current user is superuser
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create tags",
        )
    
    # Check if tag with this code already exists
    tag = await tag_service.get_tag(db, code=tag_in.code)
    if tag:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The tag with this code already exists in the system",
        )
    
    return await tag_service.create_tag(db, tag_in=tag_in)


@router.get("/{code}", response_model=Tag)
async def read_tag(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get tag by code.
    """
    tag = await tag_service.get_tag(db, code=code)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )
    return tag


@router.get("/{code}/with-user-count", response_model=TagWithUsers)
async def read_tag_with_user_count(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get tag by code with user count.
    """
    tag_with_count = await tag_service.get_tag_with_user_count(db, code=code)
    if not tag_with_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )
    
    return TagWithUsers(
        code=tag_with_count["tag"].code,
        title=tag_with_count["tag"].title,
        description=tag_with_count["tag"].description,
        created_at=tag_with_count["tag"].created_at,
        updated_at=tag_with_count["tag"].updated_at,
        user_count=tag_with_count["user_count"]
    )


@router.put("/{code}", response_model=Tag)
async def update_tag(
    code: str,
    tag_in: TagUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a tag.
    """
    # Check if current user is superuser
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update tags",
        )
    
    tag = await tag_service.get_tag(db, code=code)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )
    
    tag = await tag_service.update_tag(db, code=code, tag_in=tag_in)
    return tag


@router.delete("/{code}", response_model=Tag)
async def delete_tag(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a tag.
    """
    # Check if current user is superuser
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete tags",
        )
    
    tag = await tag_service.delete_tag(db, code=code)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )
    
    return tag


@router.get("/{code}/users", response_model=List[User])
async def read_tag_users(
    code: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all users with a specific tag.
    """
    # Check if tag exists
    tag = await tag_service.get_tag(db, code=code)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )
    
    users = await user_service.get_users_by_tag(db, tag_code=code, skip=skip, limit=limit)
    return users