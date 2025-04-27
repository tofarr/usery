from typing import Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession

from usery.api.deps import get_current_superuser
from usery.api.scim.schemas import (
    ScimUser, ScimListResponse, ScimError, ScimPatchRequest,
    ServiceProviderConfig
)
from usery.api.scim.converters import (
    user_to_scim, scim_to_user_create, scim_to_user_update, process_scim_patch
)
from usery.api.scim.filter import FilterParser
from usery.db.session import get_db
from usery.models.user import User as UserModel
from usery.api.schemas.user import User as UserSchema
from usery.services.user import (
    create_user, delete_user, get_user, get_users, update_user, count_users,
    get_user_by_email, get_user_by_username
)

router = APIRouter(prefix="/scim/v2")


@router.get("/Users", response_model=ScimListResponse)
async def list_users(
    request: Request,
    db: AsyncSession = Depends(get_db),
    startIndex: int = Query(1, ge=1),
    count: int = Query(100, ge=1),
    filter: Optional[str] = None,
    sortBy: Optional[str] = None,
    sortOrder: Optional[str] = "ascending",
    current_user: UserModel = Depends(get_current_superuser),
) -> Any:
    """
    List or search users using SCIM protocol.
    
    This endpoint supports:
    - Pagination with startIndex and count
    - Filtering with SCIM filter syntax
    - Sorting by attribute
    """
    # Convert SCIM pagination to SQLAlchemy pagination
    # SCIM uses 1-based indexing, SQLAlchemy uses 0-based
    skip = startIndex - 1
    limit = count
    
    # Base query
    query = select(UserModel)
    
    # Apply filtering if provided
    if filter:
        try:
            filter_parser = FilterParser(UserModel)
            filter_expr = filter_parser.parse(filter)
            if filter_expr is not None:
                query = query.filter(filter_expr)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid filter expression: {str(e)}"
            )
    
    # Apply sorting if provided
    if sortBy:
        # Map SCIM attribute to model attribute
        sort_attr_map = {
            "userName": UserModel.username,
            "emails.value": UserModel.email,
            "displayName": UserModel.full_name,
            "name.formatted": UserModel.full_name,
            "meta.created": UserModel.created_at,
            "meta.lastModified": UserModel.updated_at
        }
        
        sort_attr = sort_attr_map.get(sortBy)
        if sort_attr:
            if sortOrder.lower() == "ascending":
                query = query.order_by(asc(sort_attr))
            else:
                query = query.order_by(desc(sort_attr))
    
    # Get total count for pagination
    count_query = select(UserModel)
    if filter and filter_expr is not None:
        count_query = count_query.filter(filter_expr)
    
    total_results = await count_users(db, query=count_query)
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()
    
    # Convert to SCIM format
    base_url = str(request.base_url).rstrip('/')
    scim_users = [await user_to_scim(user, db, base_url) for user in users]
    
    # Return SCIM list response
    return ScimListResponse(
        totalResults=total_results,
        startIndex=startIndex,
        itemsPerPage=len(scim_users),
        Resources=scim_users
    )


@router.get("/Users/{user_id}", response_model=ScimUser)
async def get_user_by_id(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_superuser),
) -> Any:
    """
    Get a specific user using SCIM protocol.
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid user ID format"
        )
    
    user = await get_user(db, user_id=user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    base_url = str(request.base_url).rstrip('/')
    return await user_to_scim(user, db, base_url)


@router.post("/Users", response_model=ScimUser, status_code=status.HTTP_201_CREATED)
async def create_scim_user(
    scim_user: ScimUser,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_superuser),
) -> Any:
    """
    Create a new user using SCIM protocol.
    """
    try:
        # Convert SCIM user to UserCreate
        user_in = scim_to_user_create(scim_user)
        
        # Check if user with email already exists
        existing_user = await get_user_by_email(db, email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email {user_in.email} already exists"
            )
        
        # Check if user with username already exists
        existing_user = await get_user_by_username(db, username=user_in.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with username {user_in.username} already exists"
            )
        
        # Create user
        user = await create_user(db, user_in=user_in)
        
        # Convert back to SCIM format
        base_url = str(request.base_url).rstrip('/')
        return await user_to_scim(user, db, base_url)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/Users/{user_id}", response_model=ScimUser)
async def replace_user(
    user_id: str,
    scim_user: ScimUser,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_superuser),
) -> Any:
    """
    Replace a user using SCIM protocol.
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid user ID format"
        )
    
    # Check if user exists
    user = await get_user(db, user_id=user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Convert SCIM user to UserUpdate
        user_in = scim_to_user_update(scim_user)
        
        # Check email uniqueness if changing
        if user_in.email is not None and user_in.email != user.email:
            existing_user = await get_user_by_email(db, email=user_in.email)
            if existing_user and existing_user.id != user_uuid:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Email {user_in.email} already registered to another user"
                )
        
        # Check username uniqueness if changing
        if user_in.username is not None and user_in.username != user.username:
            existing_user = await get_user_by_username(db, username=user_in.username)
            if existing_user and existing_user.id != user_uuid:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Username {user_in.username} already registered to another user"
                )
        
        # Update user
        updated_user = await update_user(db, user_id=user_uuid, user_in=user_in)
        
        # Convert back to SCIM format
        base_url = str(request.base_url).rstrip('/')
        return await user_to_scim(updated_user, db, base_url)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/Users/{user_id}", response_model=ScimUser)
async def patch_user(
    user_id: str,
    patch_request: ScimPatchRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_superuser),
) -> Any:
    """
    Update a user using SCIM PATCH protocol.
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid user ID format"
        )
    
    # Check if user exists
    user = await get_user(db, user_id=user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Process PATCH operations
        operations = [op.model_dump() for op in patch_request.Operations]
        user_in = await process_scim_patch(user, operations)
        
        # Check email uniqueness if changing
        if user_in.email is not None and user_in.email != user.email:
            existing_user = await get_user_by_email(db, email=user_in.email)
            if existing_user and existing_user.id != user_uuid:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Email {user_in.email} already registered to another user"
                )
        
        # Check username uniqueness if changing
        if user_in.username is not None and user_in.username != user.username:
            existing_user = await get_user_by_username(db, username=user_in.username)
            if existing_user and existing_user.id != user_uuid:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Username {user_in.username} already registered to another user"
                )
        
        # Update user
        updated_user = await update_user(db, user_id=user_uuid, user_in=user_in)
        
        # Convert back to SCIM format
        base_url = str(request.base_url).rstrip('/')
        return await user_to_scim(updated_user, db, base_url)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/Users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scim_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_superuser),
) -> Any:
    """
    Delete a user using SCIM protocol.
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid user ID format"
        )
    
    # Check if user exists
    user = await get_user(db, user_id=user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete user
    await delete_user(db, user_id=user_uuid)
    
    # Return 204 No Content
    return None


@router.get("/ServiceProviderConfig", response_model=ServiceProviderConfig)
async def get_service_provider_config(
    request: Request,
) -> Any:
    """
    Get SCIM service provider configuration.
    """
    base_url = str(request.base_url).rstrip('/')
    
    return ServiceProviderConfig(
        documentationUri=f"{base_url}/docs",
        patch={
            "supported": True
        },
        bulk={
            "supported": True,
            "maxOperations": 100,
            "maxPayloadSize": 1048576
        },
        filter={
            "supported": True,
            "maxResults": 200
        },
        changePassword={
            "supported": True
        },
        sort={
            "supported": True
        },
        etag={
            "supported": False
        },
        authenticationSchemes=[
            {
                "type": "oauth2",
                "name": "OAuth 2.0",
                "description": "OAuth 2.0 Authentication Scheme",
                "specUri": "https://tools.ietf.org/html/rfc6749",
                "documentationUri": f"{base_url}/docs"
            }
        ]
    )