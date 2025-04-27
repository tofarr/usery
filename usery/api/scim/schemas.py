from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, HttpUrl


class ScimMeta(BaseModel):
    """SCIM Meta schema."""
    
    resourceType: str
    created: datetime
    lastModified: Optional[datetime] = None
    location: Optional[str] = None
    version: Optional[str] = None


class ScimName(BaseModel):
    """SCIM Name schema."""
    
    formatted: Optional[str] = None
    familyName: Optional[str] = None
    givenName: Optional[str] = None
    middleName: Optional[str] = None
    honorificPrefix: Optional[str] = None
    honorificSuffix: Optional[str] = None


class ScimEmail(BaseModel):
    """SCIM Email schema."""
    
    value: str
    type: Optional[str] = "work"
    primary: Optional[bool] = True
    display: Optional[str] = None


class ScimPhoto(BaseModel):
    """SCIM Photo schema."""
    
    value: HttpUrl
    type: Optional[str] = "photo"
    primary: Optional[bool] = True


class ScimUserBase(BaseModel):
    """Base SCIM User schema."""
    
    schemas: List[str] = ["urn:ietf:params:scim:schemas:core:2.0:User"]
    userName: str
    name: Optional[ScimName] = None
    displayName: Optional[str] = None
    emails: List[ScimEmail] = []
    active: bool = True
    photos: Optional[List[ScimPhoto]] = None
    externalId: Optional[str] = None


class ScimUser(ScimUserBase):
    """SCIM User schema."""
    
    id: str
    meta: ScimMeta


class ScimListResponse(BaseModel):
    """SCIM List Response schema."""
    
    schemas: List[str] = ["urn:ietf:params:scim:schemas:core:2.0:ListResponse"]
    totalResults: int
    startIndex: int
    itemsPerPage: int
    Resources: List[Any] = []


class ScimError(BaseModel):
    """SCIM Error schema."""
    
    schemas: List[str] = ["urn:ietf:params:scim:api:messages:2.0:Error"]
    status: str
    scimType: Optional[str] = None
    detail: str


class ScimPatchOperation(BaseModel):
    """SCIM Patch Operation schema."""
    
    op: str = Field(..., description="The operation to perform")
    path: Optional[str] = Field(None, description="A JSON Pointer path")
    value: Optional[Any] = Field(None, description="The value to be used for the operation")


class ScimPatchRequest(BaseModel):
    """SCIM Patch Request schema."""
    
    schemas: List[str] = ["urn:ietf:params:scim:api:messages:2.0:PatchOp"]
    Operations: List[ScimPatchOperation]


class ServiceProviderConfig(BaseModel):
    """SCIM Service Provider Configuration schema."""
    
    schemas: List[str] = ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"]
    documentationUri: Optional[HttpUrl] = None
    patch: Dict[str, Any]
    bulk: Dict[str, Any]
    filter: Dict[str, Any]
    changePassword: Dict[str, Any]
    sort: Dict[str, Any]
    etag: Dict[str, Any]
    authenticationSchemes: List[Dict[str, Any]]