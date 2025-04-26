from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from redis.client import Redis
from sqlalchemy.orm import Session

from usery.api.schemas.auth import Token, Login
from usery.config.settings import settings
from usery.db.redis import get_redis
from usery.db.session import get_db
from usery.services.security import create_access_token, store_token_in_blacklist
from usery.services.user import authenticate_user

router = APIRouter()


@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/login/json", response_model=Token)
def login_json(
    *,
    db: Session = Depends(get_db),
    login_in: Login,
) -> Any:
    """
    JSON compatible login, get an access token for future requests.
    """
    user = authenticate_user(db, login_in.username, login_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/logout")
def logout(
    *,
    token: str,
    redis_client: Redis = Depends(get_redis),
) -> Any:
    """
    Logout by blacklisting the token.
    """
    store_token_in_blacklist(
        redis_client, token, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return {"message": "Successfully logged out"}