from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from usery.api.deps import get_current_active_user
from usery.api.schemas.user import User, UserCreate, UserUpdate
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
)

router = APIRouter()


@router.get("/", response_model=List[User])
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve users.
    """
    users = get_users(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_new_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create new user.
    """
    user = get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    
    user = get_user_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this username already exists in the system.",
        )
    
    user = create_user(db, user_in=user_in)
    return user


@router.get("/{user_id}", response_model=User)
def read_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
) -> Any:
    """
    Get a specific user by id.
    """
    user = get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.put("/{user_id}", response_model=User)
def update_user_info(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """
    user = get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if user_in.email is not None and user_in.email != user.email:
        existing_user = get_user_by_email(db, email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
    
    if user_in.username is not None and user_in.username != user.username:
        existing_user = get_user_by_username(db, username=user_in.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )
    
    user = update_user(db, user_id=user_id, user_in=user_in)
    return user


@router.delete("/{user_id}", response_model=User)
def delete_user_by_id(
    *,
    db: Session = Depends(get_db),
    user_id: int,
) -> Any:
    """
    Delete a user.
    """
    user = get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    user = delete_user(db, user_id=user_id)
    return user