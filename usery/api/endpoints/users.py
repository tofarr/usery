from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from usery.api.deps import get_current_active_user, get_current_superuser
from usery.api.schemas.user import User, UserCreate, UserUpdate, UserWithTags
from usery.api.schemas.batch import BatchRequest, BatchResponse, BatchResponseItem, BatchOperationType
from usery.config.settings import settings
from usery.db.session import get_db
from usery.models.user import User as UserModel
from usery.services.user import (
    create_user,
    delete_user,
    get_user,
    get_user_by_email,
    get_user_by_username,
    get_users,
    update_user,
    get_user_with_tags,
)

router = APIRouter()


@router.get("/", response_model=List[User])
async def read_users(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve users.
    """
    users = await get_users(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_new_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate,
    current_user: UserModel = Depends(get_current_superuser) if settings.SUPERUSER_ONLY_CREATE_USERS else None,
) -> Any:
    """
    Create new user.
    
    If SUPERUSER_ONLY_CREATE_USERS setting is True, only superusers can create new users.
    Otherwise, anyone can register.
    """
    # If SUPERUSER_ONLY_CREATE_USERS is True, the dependency will ensure only superusers can access this endpoint
    
    user = await get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    
    user = await get_user_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this username already exists in the system.",
        )
    
    user = await create_user(db, user_in=user_in)
    return user


@router.get("/{user_id}", response_model=User)
async def read_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
) -> Any:
    """
    Get a specific user by id.
    """
    user = await get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.get("/{user_id}/with-tags", response_model=UserWithTags)
async def read_user_with_tags(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Get a specific user by id with their tags.
    """
    result = await get_user_with_tags(db, user_id=user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return UserWithTags(
        id=result["user"].id,
        email=result["user"].email,
        username=result["user"].username,
        full_name=result["user"].full_name,
        is_active=result["user"].is_active,
        created_at=result["user"].created_at,
        updated_at=result["user"].updated_at,
        tags=result["tags"]
    )


@router.put("/{user_id}", response_model=User)
async def update_user_info(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
    user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """
    user = await get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if user_in.email is not None and user_in.email != user.email:
        existing_user = await get_user_by_email(db, email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
    
    if user_in.username is not None and user_in.username != user.username:
        existing_user = await get_user_by_username(db, username=user_in.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )
    
    user = await update_user(db, user_id=user_id, user_in=user_in)
    return user


@router.delete("/{user_id}", response_model=User)
async def delete_user_by_id(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
) -> Any:
    """
    Delete a user.
    """
    user = await get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    user = await delete_user(db, user_id=user_id)
    return user


@router.post("/batch", response_model=BatchResponse)
async def batch_users_operations(
    *,
    db: AsyncSession = Depends(get_db),
    batch_request: BatchRequest[UserCreate | UserUpdate],
    current_user: UserModel = Depends(get_current_superuser),
) -> Any:
    """
    Perform batch operations on users (create, update, delete).
    Only superusers can perform batch operations.
    """
    results = []
    success_count = 0
    error_count = 0

    for index, operation in enumerate(batch_request.operations):
        try:
            if operation.operation == BatchOperationType.CREATE:
                if not operation.data:
                    raise ValueError("Data is required for create operation")
                
                # Check if user with email already exists
                user_data = operation.data
                existing_user = await get_user_by_email(db, email=user_data.email)
                if existing_user:
                    raise ValueError(f"User with email {user_data.email} already exists")
                
                # Check if user with username already exists
                existing_user = await get_user_by_username(db, username=user_data.username)
                if existing_user:
                    raise ValueError(f"User with username {user_data.username} already exists")
                
                user = await create_user(db, user_in=user_data)
                results.append(BatchResponseItem(
                    success=True,
                    data=user,
                    index=index
                ))
                success_count += 1
                
            elif operation.operation == BatchOperationType.UPDATE:
                if not operation.id:
                    raise ValueError("ID is required for update operation")
                if not operation.data:
                    raise ValueError("Data is required for update operation")
                
                user_id = operation.id
                user_data = operation.data
                
                # Check if user exists
                user = await get_user(db, user_id=user_id)
                if not user:
                    raise ValueError(f"User with ID {user_id} not found")
                
                # Check for email uniqueness if changing email
                if user_data.email is not None and user_data.email != user.email:
                    existing_user = await get_user_by_email(db, email=user_data.email)
                    if existing_user:
                        raise ValueError(f"Email {user_data.email} already registered")
                
                # Check for username uniqueness if changing username
                if user_data.username is not None and user_data.username != user.username:
                    existing_user = await get_user_by_username(db, username=user_data.username)
                    if existing_user:
                        raise ValueError(f"Username {user_data.username} already registered")
                
                updated_user = await update_user(db, user_id=user_id, user_in=user_data)
                results.append(BatchResponseItem(
                    success=True,
                    data=updated_user,
                    index=index
                ))
                success_count += 1
                
            elif operation.operation == BatchOperationType.DELETE:
                if not operation.id:
                    raise ValueError("ID is required for delete operation")
                
                user_id = operation.id
                
                # Check if user exists
                user = await get_user(db, user_id=user_id)
                if not user:
                    raise ValueError(f"User with ID {user_id} not found")
                
                deleted_user = await delete_user(db, user_id=user_id)
                results.append(BatchResponseItem(
                    success=True,
                    data=deleted_user,
                    index=index
                ))
                success_count += 1
                
            else:
                raise ValueError(f"Unknown operation type: {operation.operation}")
                
        except Exception as e:
            results.append(BatchResponseItem(
                success=False,
                error=str(e),
                index=index
            ))
            error_count += 1
    
    return BatchResponse(
        results=results,
        success_count=success_count,
        error_count=error_count
    )