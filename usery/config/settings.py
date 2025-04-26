import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Usery"
    
    # Database settings
    DATABASE_URL: str = Field(
        default="sqlite:///./usery.db", 
        description="Database connection string"
    )
    SQL_ECHO: bool = Field(
        default=False,
        description="Enable SQL query logging"
    )
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Security settings
    SECRET_KEY: str = Field(
        default="supersecretkey",
        description="Secret key for JWT token generation"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()