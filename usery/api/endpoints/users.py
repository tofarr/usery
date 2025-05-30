from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from usery.api.deps import get_current_active_user, get_current_superuser, get_user_visibility_dependency
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
    count_users,
)

router = APIRouter()


@router.get("/", response_model=List[User])
async def read_users(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    _: Any = Depends(get_user_visibility_dependency()),
) -> Any:
    """
    Retrieve users.
    
    Access depends on USER_VISIBILITY setting:
    - 'private': Only superusers can list users
    - 'protected': Only active users can list users
    - 'public': No login required to list users
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
    
    Special case: If there are no users in the system, the first user created will
    automatically be a superuser, regardless of the SUPERUSER_ONLY_CREATE_USERS setting.
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
    
    # Check if this is the first user being created
    user_count = await count_users(db)
    if user_count == 0:
        # First user must be a superuser
        user_in.is_superuser = True
    
    user = await create_user(db, user_in=user_in)
    return user


@router.get("/{user_id}", response_model=User)
async def read_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Get a specific user by id.
    
    Users can always view their own profile.
    For other users, access depends on USER_VISIBILITY setting and user permissions.
    """
    user = await get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check if user has permission to view this profile
    if user_id != current_user.id:  # Not viewing own profile
        if settings.USER_VISIBILITY == "private" and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view this user",
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
    
    Users can always view their own profile with tags.
    For other users, access depends on USER_VISIBILITY setting and user permissions.
    """
    result = await get_user_with_tags(db, user_id=user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check if user has permission to view this profile
    if user_id != current_user.id:  # Not viewing own profile
        if settings.USER_VISIBILITY == "private" and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view this user",
            )
    
    return UserWithTags(
        id=result["user"].id,
        email=result["user"].email,
        username=result["user"].username,
        full_name=result["user"].full_name,
        avatar_url=result["user"].avatar_url,
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
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Update a user.
    
    Only superusers can update the is_superuser flag.
    Superusers cannot remove their own superuser status.
    """
    user = await get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check if the current user has permission to update this user
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this user",
        )
    
    # Handle superuser flag changes
    if user_in.is_superuser is not None:
        # Only superusers can change the superuser flag
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superusers can change the superuser status",
            )
        
        # Superusers cannot remove their own superuser status
        if current_user.id == user_id and user_in.is_superuser is False:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Superusers cannot remove their own superuser status",
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
                
                # Check if this is the first user being created
                user_count = await count_users(db)
                if user_count == 0:
                    # First user must be a superuser
                    user_data.is_superuser = True
                
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
                
                # Handle superuser flag changes
                if user_data.is_superuser is not None:
                    # Superusers cannot remove their own superuser status
                    if current_user.id == user_id and user_data.is_superuser is False:
                        raise ValueError("Superusers cannot remove their own superuser status")
                
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