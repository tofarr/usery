from fastapi import APIRouter

from usery.api.endpoints import auth, users, tags, user_tags, attributes, user_attributes, clients, key_pairs, oidc, avatars

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(user_tags.router, tags=["user_tags"])
api_router.include_router(attributes.router, prefix="/attributes", tags=["attributes"])
api_router.include_router(user_attributes.router, tags=["user_attributes"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(key_pairs.router, prefix="/key-pairs", tags=["key_pairs"])
api_router.include_router(oidc.router, prefix="/oidc", tags=["oidc"])
api_router.include_router(avatars.router, prefix="/avatars", tags=["avatars"])

# Add the OpenID Connect Discovery endpoint at the root level
api_router.include_router(oidc.router, tags=["oidc"])