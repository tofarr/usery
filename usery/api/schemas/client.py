from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, UUID4, Field, AnyHttpUrl


class ClientBase(BaseModel):
    """Base client schema."""
    
    title: str
    description: Optional[str] = None
    access_token_timeout: int = Field(3600, description="Access token timeout in seconds")
    refresh_token_timeout: int = Field(86400, description="Refresh token timeout in seconds")
    
    # OIDC specific fields
    client_type: Literal["confidential", "public"] = "confidential"
    redirect_uris: List[str] = Field(default_factory=list, description="List of allowed redirect URIs")
    allowed_scopes: List[str] = Field(default_factory=lambda: ["openid"], description="List of allowed scopes")
    response_types: List[str] = Field(default_factory=lambda: ["code"], description="Allowed response types (code, token, id_token)")
    grant_types: List[str] = Field(default_factory=lambda: ["authorization_code"], description="Allowed grant types")
    token_endpoint_auth_method: Literal["client_secret_basic", "client_secret_post", "none"] = "client_secret_basic"
    id_token_signed_response_alg: str = "RS256"
    require_pkce: bool = False
    allow_offline_access: bool = False


class ClientCreate(ClientBase):
    """Schema for creating a client."""
    pass


class ClientUpdate(BaseModel):
    """Schema for updating a client."""
    
    title: Optional[str] = None
    description: Optional[str] = None
    access_token_timeout: Optional[int] = None
    refresh_token_timeout: Optional[int] = None
    
    # OIDC specific fields
    client_type: Optional[Literal["confidential", "public"]] = None
    redirect_uris: Optional[List[str]] = None
    allowed_scopes: Optional[List[str]] = None
    response_types: Optional[List[str]] = None
    grant_types: Optional[List[str]] = None
    token_endpoint_auth_method: Optional[Literal["client_secret_basic", "client_secret_post", "none"]] = None
    id_token_signed_response_alg: Optional[str] = None
    require_pkce: Optional[bool] = None
    allow_offline_access: Optional[bool] = None


class ClientInDBBase(ClientBase):
    """Base schema for clients in DB."""
    
    id: UUID4
    client_secret: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Client(ClientInDBBase):
    """Schema for client response."""
    pass