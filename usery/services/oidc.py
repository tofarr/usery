from datetime import datetime, timedelta
import hashlib
import base64
import json
import os
from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import UUID

from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from usery.config.settings import settings
from usery.models.client import Client
from usery.models.user import User
from usery.services.authorization_code import create_authorization_code, get_valid_authorization_code, mark_code_as_used
from usery.services.refresh_token import create_refresh_token, get_valid_refresh_token, revoke_refresh_token
from usery.services.client import get_client
from usery.services.user import get_user
from usery.services.consent import has_user_consented_to_scopes, get_consented_scopes, create_consent
from usery.services.key_pair import get_active_key_pairs
from usery.api.schemas.authorization_code import AuthorizationCodeCreate
from usery.api.schemas.refresh_token import RefreshTokenCreate
from usery.api.schemas.consent import ConsentCreate


# PKCE (Proof Key for Code Exchange) functions
def verify_code_challenge(code_verifier: str, code_challenge: str, code_challenge_method: str) -> bool:
    """Verify the code challenge with the code verifier."""
    if code_challenge_method == "plain":
        return code_verifier == code_challenge
    elif code_challenge_method == "S256":
        hashed = hashlib.sha256(code_verifier.encode()).digest()
        encoded = base64.urlsafe_b64encode(hashed).decode().rstrip("=")
        return encoded == code_challenge
    else:
        return False


# Scope handling functions
def parse_scopes(scope_string: str) -> Set[str]:
    """Parse a space-separated scope string into a set of scopes."""
    if not scope_string:
        return set()
    return set(scope_string.split())


def join_scopes(scopes: Set[str]) -> str:
    """Join a set of scopes into a space-separated string."""
    return " ".join(sorted(scopes))


# ID Token functions
async def create_id_token(
    db: AsyncSession,
    client: Client,
    user: User,
    nonce: Optional[str] = None,
    auth_time: Optional[datetime] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
    access_token: Optional[str] = None,
    code: Optional[str] = None,
    expires_in: int = 3600  # Default 1 hour
) -> str:
    """Create an ID token (JWT) for the user."""
    now = datetime.utcnow()
    
    # Get the signing key
    key_pairs = await get_active_key_pairs(db)
    if not key_pairs:
        # If no key pairs exist, use the JWT secret key as a fallback
        # This is not ideal for production, but allows the system to work without key pairs
        from usery.services.security import _JWT_SECRET_KEY
        
        # Create the payload
        payload = {
            "iss": f"{settings.SERVER_HOST}/",  # Issuer
            "sub": str(user.id),  # Subject (user ID)
            "aud": str(client.id),  # Audience (client ID)
            "exp": now + timedelta(seconds=expires_in),  # Expiration time
            "iat": now,  # Issued at
            "auth_time": auth_time or now,  # Time when authentication occurred
        }
        
        # Add optional claims
        if nonce:
            payload["nonce"] = nonce
        
        # Add standard claims
        if "profile" in parse_scopes(client.allowed_scopes):
            payload.update({
                "name": user.full_name,
                "preferred_username": user.username,
            })
        
        if "email" in parse_scopes(client.allowed_scopes):
            payload.update({
                "email": user.email,
                "email_verified": user.is_verified,
            })
        
        # Add extra claims
        if extra_claims:
            payload.update(extra_claims)
        
        # Add at_hash if access_token is provided
        if access_token:
            # Calculate at_hash (Access Token hash)
            at_hash = hashlib.sha256(access_token.encode()).digest()
            at_hash_half = at_hash[:len(at_hash) // 2]
            at_hash_b64 = base64.urlsafe_b64encode(at_hash_half).decode().rstrip("=")
            payload["at_hash"] = at_hash_b64
        
        # Add c_hash if code is provided
        if code:
            # Calculate c_hash (Code hash)
            c_hash = hashlib.sha256(code.encode()).digest()
            c_hash_half = c_hash[:len(c_hash) // 2]
            c_hash_b64 = base64.urlsafe_b64encode(c_hash_half).decode().rstrip("=")
            payload["c_hash"] = c_hash_b64
        
        # Sign the token with HS256 algorithm
        return jwt.encode(payload, _JWT_SECRET_KEY, algorithm="HS256")
    else:
        # Use the first active key pair for signing
        key_pair = key_pairs[0]
        
        # Create the payload
        payload = {
            "iss": f"{settings.SERVER_HOST}/",  # Issuer
            "sub": str(user.id),  # Subject (user ID)
            "aud": str(client.id),  # Audience (client ID)
            "exp": now + timedelta(seconds=expires_in),  # Expiration time
            "iat": now,  # Issued at
            "auth_time": auth_time or now,  # Time when authentication occurred
        }
        
        # Add optional claims
        if nonce:
            payload["nonce"] = nonce
        
        # Add standard claims
        if "profile" in parse_scopes(client.allowed_scopes):
            payload.update({
                "name": user.full_name,
                "preferred_username": user.username,
            })
        
        if "email" in parse_scopes(client.allowed_scopes):
            payload.update({
                "email": user.email,
                "email_verified": user.is_verified,
            })
        
        # Add extra claims
        if extra_claims:
            payload.update(extra_claims)
        
        # Add at_hash if access_token is provided
        if access_token:
            # Calculate at_hash (Access Token hash)
            at_hash = hashlib.sha256(access_token.encode()).digest()
            at_hash_half = at_hash[:len(at_hash) // 2]
            at_hash_b64 = base64.urlsafe_b64encode(at_hash_half).decode().rstrip("=")
            payload["at_hash"] = at_hash_b64
        
        # Add c_hash if code is provided
        if code:
            # Calculate c_hash (Code hash)
            c_hash = hashlib.sha256(code.encode()).digest()
            c_hash_half = c_hash[:len(c_hash) // 2]
            c_hash_b64 = base64.urlsafe_b64encode(c_hash_half).decode().rstrip("=")
            payload["c_hash"] = c_hash_b64
        
        # Sign the token with the specified algorithm
        return jwt.encode(payload, key_pair.private_key, algorithm=client.id_token_signed_response_alg)


# Authorization Code Flow functions
async def create_authorization_code_flow(
    db: AsyncSession,
    client_id: UUID,
    user_id: UUID,
    redirect_uri: str,
    scope: str,
    nonce: Optional[str] = None,
    code_challenge: Optional[str] = None,
    code_challenge_method: Optional[str] = None,
    expires_in: int = 600  # Default 10 minutes
) -> str:
    """Create an authorization code for the authorization code flow."""
    # Create the authorization code
    code_in = AuthorizationCodeCreate(
        client_id=client_id,
        user_id=user_id,
        redirect_uri=redirect_uri,
        scope=scope,
        nonce=nonce,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        expires_at=datetime.utcnow() + timedelta(seconds=expires_in)
    )
    
    auth_code = await create_authorization_code(db, code_in)
    return auth_code.code


async def exchange_authorization_code(
    db: AsyncSession,
    code: str,
    client_id: UUID,
    redirect_uri: str,
    code_verifier: Optional[str] = None
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[int], Optional[str]]:
    """
    Exchange an authorization code for tokens.
    
    Returns:
        Tuple of (access_token, refresh_token, id_token, expires_in, scope)
        or (None, None, None, None, None) if the exchange fails.
    """
    # Get the authorization code
    auth_code = await get_valid_authorization_code(db, code)
    if not auth_code:
        return None, None, None, None, None
    
    # Verify the client ID
    if auth_code.client_id != client_id:
        return None, None, None, None, None
    
    # Verify the redirect URI
    if auth_code.redirect_uri != redirect_uri:
        return None, None, None, None, None
    
    # Verify the PKCE code challenge if present
    if auth_code.code_challenge and auth_code.code_challenge_method:
        if not code_verifier or not verify_code_challenge(
            code_verifier, 
            auth_code.code_challenge, 
            auth_code.code_challenge_method
        ):
            return None, None, None, None, None
    
    # Mark the code as used
    await mark_code_as_used(db, code)
    
    # Get the client and user
    client = await get_client(db, client_id)
    user = await get_user(db, auth_code.user_id)
    
    if not client or not user:
        return None, None, None, None, None
    
    # Create an access token
    from usery.services.security import create_access_token
    access_token = create_access_token(
        user.id,
        expires_delta=timedelta(seconds=client.access_token_timeout)
    )
    
    # Create a refresh token if allowed
    refresh_token = None
    if client.allow_offline_access and "offline_access" in parse_scopes(auth_code.scope):
        token_in = RefreshTokenCreate(
            client_id=client_id,
            user_id=user.id,
            scope=auth_code.scope,
            expires_at=datetime.utcnow() + timedelta(seconds=client.refresh_token_timeout)
        )
        refresh_token_obj = await create_refresh_token(db, token_in)
        refresh_token = refresh_token_obj.token
    
    # Create an ID token if requested
    id_token = None
    if "openid" in parse_scopes(auth_code.scope):
        id_token = await create_id_token(
            db,
            client,
            user,
            nonce=auth_code.nonce,
            auth_time=auth_code.auth_time,
            extra_claims=auth_code.claims,
            access_token=access_token,
            code=code,
            expires_in=client.access_token_timeout
        )
    
    return access_token, refresh_token, id_token, client.access_token_timeout, auth_code.scope


# Refresh Token Flow functions
async def refresh_tokens(
    db: AsyncSession,
    refresh_token: str,
    client_id: UUID,
    scope: Optional[str] = None
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[int], Optional[str]]:
    """
    Refresh tokens using a refresh token.
    
    Returns:
        Tuple of (access_token, refresh_token, id_token, expires_in, scope)
        or (None, None, None, None, None) if the refresh fails.
    """
    # Get the refresh token
    token = await get_valid_refresh_token(db, refresh_token)
    if not token:
        return None, None, None, None, None
    
    # Verify the client ID
    if token.client_id != client_id:
        return None, None, None, None, None
    
    # Get the client and user
    client = await get_client(db, client_id)
    user = await get_user(db, token.user_id)
    
    if not client or not user:
        return None, None, None, None, None
    
    # Determine the scope
    token_scope = token.scope
    if scope:
        # If a scope is requested, it must be a subset of the original scope
        requested_scopes = parse_scopes(scope)
        original_scopes = parse_scopes(token_scope)
        
        if not requested_scopes.issubset(original_scopes):
            return None, None, None, None, None
        
        # Use the requested scope
        token_scope = scope
    
    # Create a new access token
    from usery.services.security import create_access_token
    access_token = create_access_token(
        user.id,
        expires_delta=timedelta(seconds=client.access_token_timeout)
    )
    
    # Revoke the old refresh token and create a new one if offline_access is in scope
    new_refresh_token = None
    if "offline_access" in parse_scopes(token_scope):
        # Revoke the old token
        await revoke_refresh_token(db, refresh_token)
        
        # Create a new refresh token
        token_in = RefreshTokenCreate(
            client_id=client_id,
            user_id=user.id,
            scope=token_scope,
            expires_at=datetime.utcnow() + timedelta(seconds=client.refresh_token_timeout)
        )
        new_token = await create_refresh_token(db, token_in)
        new_refresh_token = new_token.token
    
    # Create an ID token if openid is in scope
    id_token = None
    if "openid" in parse_scopes(token_scope):
        id_token = await create_id_token(
            db,
            client,
            user,
            access_token=access_token,
            expires_in=client.access_token_timeout
        )
    
    return access_token, new_refresh_token, id_token, client.access_token_timeout, token_scope


# Consent functions
async def ensure_user_consent(
    db: AsyncSession,
    user_id: UUID,
    client_id: UUID,
    requested_scopes: Set[str]
) -> bool:
    """
    Ensure the user has consented to the requested scopes.
    
    Returns:
        True if the user has already consented to all requested scopes,
        False if consent is needed.
    """
    # Check if the user has already consented to all requested scopes
    if await has_user_consented_to_scopes(db, user_id, client_id, list(requested_scopes)):
        return True
    
    return False


async def record_user_consent(
    db: AsyncSession,
    user_id: UUID,
    client_id: UUID,
    scopes: Set[str]
) -> None:
    """Record the user's consent to the specified scopes."""
    # Get existing consented scopes
    existing_scopes = await get_consented_scopes(db, user_id, client_id)
    
    # Combine with new scopes
    all_scopes = existing_scopes.union(scopes)
    
    # Create a new consent record
    consent_in = ConsentCreate(
        user_id=user_id,
        client_id=client_id,
        scopes=list(all_scopes)
    )
    
    await create_consent(db, consent_in)


# JWKS (JSON Web Key Set) functions
async def get_jwks(db: AsyncSession) -> Dict[str, Any]:
    """Get the JWKS (JSON Web Key Set) for the server."""
    key_pairs = await get_active_key_pairs(db)
    
    keys = []
    for key_pair in key_pairs:
        if key_pair.algorithm.startswith("RS"):
            # For RSA keys
            # Note: This is a simplified example. In a real implementation,
            # you would need to parse the private key to extract the modulus and exponent.
            keys.append({
                "kty": "RSA",
                "use": "sig",
                "kid": str(key_pair.id),
                "alg": key_pair.algorithm,
                "n": "...",  # Base64URL-encoded modulus
                "e": "AQAB",  # Base64URL-encoded exponent (usually AQAB for e=65537)
            })
    
    return {"keys": keys}


# OpenID Connect Discovery document
async def get_discovery_document(db: AsyncSession) -> Dict[str, Any]:
    """Get the OpenID Connect Discovery document."""
    base_url = f"{settings.SERVER_HOST}"
    
    return {
        "issuer": f"{base_url}/",
        "authorization_endpoint": f"{base_url}/oidc/authorize",
        "token_endpoint": f"{base_url}/oidc/token",
        "userinfo_endpoint": f"{base_url}/oidc/userinfo",
        "jwks_uri": f"{base_url}/oidc/jwks",
        "registration_endpoint": f"{base_url}/oidc/register",
        "scopes_supported": ["openid", "profile", "email", "offline_access"],
        "response_types_supported": ["code", "token", "id_token", "code token", "code id_token", "token id_token", "code token id_token"],
        "grant_types_supported": ["authorization_code", "implicit", "refresh_token", "client_credentials"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256", "HS256"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post", "none"],
        "claims_supported": ["sub", "iss", "auth_time", "name", "preferred_username", "email", "email_verified"],
        "code_challenge_methods_supported": ["plain", "S256"],
    }