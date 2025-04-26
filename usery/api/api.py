from fastapi import APIRouter

from usery.api.endpoints import auth, users, tags, user_tags

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(user_tags.router, tags=["user_tags"])