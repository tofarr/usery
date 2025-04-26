from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from usery.api.api import api_router
from usery.config.settings import settings
from usery.db.redis import create_redis_pool

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup."""
    # Initialize Redis pool
    app.state.redis = await create_redis_pool()


@app.on_event("shutdown")
async def shutdown_event():
    """Close connections on shutdown."""
    # Close Redis pool
    if hasattr(app.state, "redis"):
        await app.state.redis.close()


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}