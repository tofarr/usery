from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from usery.api.scim.schemas import ScimUser, ScimName, ScimEmail, ScimMeta, ScimPhoto
from usery.api.schemas.user import UserCreate, UserUpdate
from usery.models.user import User
from usery.services.user_attribute import get_user_attributes


async def user_to_scim(user: User, db: AsyncSession, base_url: str) -> ScimUser:
    """Convert a User model to a SCIM User."""
    # Get user attributes (for future extension)
    # user_attrs = await get_user_attributes(db, user.id)
    
    # Create emails list
    emails = [ScimEmail(value=user.email, primary=True, type="work")]
    
    # Create photos list if avatar_url exists
    photos = None
    if user.avatar_url:
        try:
            photos = [ScimPhoto(value=user.avatar_url, primary=True, type="photo")]
        except:
            # If the URL is invalid, skip it
            pass
    
    # Create name object
    name = None
    if user.full_name:
        # Simple mapping - in a real implementation, you might want to parse the full name
        name = ScimName(formatted=user.full_name)
    
    # Create meta
    meta = ScimMeta(
        resourceType="User",
        created=user.created_at,
        lastModified=user.updated_at,
        location=f"{base_url}/scim/v2/Users/{user.id}"
    )
    
    # Create SCIM user
    scim_user = ScimUser(
        id=str(user.id),
        userName=user.username,
        displayName=user.full_name,
        name=name,
        emails=emails,
        active=user.is_active,
        photos=photos,
        meta=meta
    )
    
    return scim_user


def scim_to_user_create(scim_user: ScimUser) -> UserCreate:
    """Convert a SCIM User to UserCreate model."""
    # Extract email from emails list
    email = next((e.value for e in scim_user.emails if e.primary), 
                 scim_user.emails[0].value if scim_user.emails else None)
    
    if not email:
        raise ValueError("Email is required")
    
    # Extract full name
    full_name = None
    if scim_user.name and scim_user.name.formatted:
        full_name = scim_user.name.formatted
    elif scim_user.displayName:
        full_name = scim_user.displayName
    
    # Create UserCreate object
    # Note: password is required but not part of SCIM - would need to be handled separately
    # or generated and sent to the user
    user_create = UserCreate(
        email=email,
        username=scim_user.userName,
        full_name=full_name,
        is_active=scim_user.active,
        # Generate a random password - in a real implementation, you might want to
        # send this to the user or require it to be set separately
        password="TemporaryPassword123!"  # This should be changed by the user
    )
    
    return user_create


def scim_to_user_update(scim_user: ScimUser) -> UserUpdate:
    """Convert a SCIM User to UserUpdate model."""
    # Extract email from emails list if present
    email = None
    if scim_user.emails:
        email = next((e.value for e in scim_user.emails if e.primary), 
                     scim_user.emails[0].value)
    
    # Extract full name
    full_name = None
    if scim_user.name and scim_user.name.formatted:
        full_name = scim_user.name.formatted
    elif scim_user.displayName:
        full_name = scim_user.displayName
    
    # Extract avatar URL
    avatar_url = None
    if scim_user.photos:
        avatar_url = next((p.value.unicode_string() for p in scim_user.photos if p.primary), 
                          scim_user.photos[0].value.unicode_string() if scim_user.photos else None)
    
    # Create UserUpdate object
    user_update = UserUpdate(
        email=email,
        username=scim_user.userName,
        full_name=full_name,
        avatar_url=avatar_url,
        is_active=scim_user.active
    )
    
    # Remove None values
    update_data = {k: v for k, v in user_update.model_dump().items() if v is not None}
    
    return UserUpdate(**update_data)


async def process_scim_patch(user: User, operations: List[Dict[str, Any]]) -> UserUpdate:
    """Process SCIM PATCH operations and return a UserUpdate object."""
    # Start with an empty update
    update_data = {}
    
    for op in operations:
        operation = op.get("op", "").lower()
        path = op.get("path", "")
        value = op.get("value")
        
        # Handle different operations
        if operation == "add" or operation == "replace":
            # Map SCIM paths to User model attributes
            if path == "userName":
                update_data["username"] = value
            elif path == "emails[type eq \"work\"].value" or path == "emails.value":
                update_data["email"] = value
            elif path == "name.formatted" or path == "displayName":
                update_data["full_name"] = value
            elif path == "active":
                update_data["is_active"] = value
            elif path == "photos[type eq \"photo\"].value" or path == "photos.value":
                update_data["avatar_url"] = value
        
        elif operation == "remove":
            # Handle removal of attributes
            if path == "name.formatted" or path == "displayName":
                update_data["full_name"] = None
            elif path == "photos[type eq \"photo\"].value" or path == "photos.value":
                update_data["avatar_url"] = None
    
    return UserUpdate(**update_data)