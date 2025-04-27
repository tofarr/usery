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
        description="Secret key for JWT token generation (used for HS256)"
    )
    JWT_PRIVATE_KEY: Optional[str] = Field(
        default=None,
        description="RSA private key for JWT token signing (used for RS256)"
    )
    JWT_PUBLIC_KEY: Optional[str] = Field(
        default=None,
        description="RSA public key for JWT token verification (used for RS256)"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SUPERUSER_ONLY_CREATE_USERS: bool = Field(
        default=False,
        description="If True, only superusers can create new users. If False, anyone can register."
    )
    USER_VISIBILITY: str = Field(
        default="protected",
        description="""Controls who can view user information:
        - 'private': Only superusers can list users. Users can view themselves.
        - 'protected': Only active users can list users. Users can view themselves.
        - 'public': No login required to list users."""
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()