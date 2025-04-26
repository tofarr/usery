from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from usery.api.api import api_router
from usery.config.settings import settings

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


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}