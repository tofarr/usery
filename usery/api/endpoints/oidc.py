from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status, Form
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse

from usery.api.deps import get_current_user, get_db
from usery.config.settings import settings
from usery.models.user import User as UserModel
from usery.services.client import get_client
from usery.services.oidc import (
    create_authorization_code_flow,
    exchange_authorization_code,
    refresh_tokens,
    ensure_user_consent,
    record_user_consent,
    get_jwks,
    get_discovery_document,
    parse_scopes,
    join_scopes,
    create_id_token,
)

router = APIRouter()


@router.get("/.well-known/openid-configuration")
async def openid_configuration(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    OpenID Connect Discovery endpoint.
    
    Returns the OpenID Connect Discovery document.
    """
    return await get_discovery_document(db)


@router.get("/jwks")
async def jwks(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    JSON Web Key Set (JWKS) endpoint.
    
    Returns the public keys used to verify ID tokens.
    """
    return await get_jwks(db)


@router.get("/authorize")
async def authorize(
    response_type: str = Query(..., description="The type of response requested"),
    client_id: UUID = Query(..., description="The client identifier"),
    redirect_uri: str = Query(..., description="The URI to redirect to after authorization"),
    scope: str = Query(..., description="The scope of the access request"),
    state: Optional[str] = Query(None, description="Value used to maintain state between the request and callback"),
    nonce: Optional[str] = Query(None, description="String value used to associate a client session with an ID Token"),
    code_challenge: Optional[str] = Query(None, description="PKCE code challenge"),
    code_challenge_method: Optional[str] = Query(None, description="PKCE code challenge method"),
    prompt: Optional[str] = Query(None, description="Specifies whether the authorization server prompts the user for reauthentication"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user),
) -> Any:
    """
    Authorization endpoint.
    
    This endpoint is used to interact with the resource owner and obtain an authorization grant.
    """
    # Check if the client exists
    client = await get_client(db, client_id=client_id)
    if not client:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "invalid_client", "error_description": "Client not found"}
        )
    
    # Check if the redirect URI is allowed
    if redirect_uri not in client.redirect_uris:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "invalid_request", "error_description": "Redirect URI not allowed"}
        )
    
    # Check if the response type is allowed
    if response_type not in client.response_types:
        return RedirectResponse(
            f"{redirect_uri}?error=unsupported_response_type&error_description=Response+type+not+allowed&state={state or ''}"
        )
    
    # Parse and validate scopes
    requested_scopes = parse_scopes(scope)
    allowed_scopes = set(client.allowed_scopes)
    
    if not requested_scopes.issubset(allowed_scopes):
        return RedirectResponse(
            f"{redirect_uri}?error=invalid_scope&error_description=Scope+not+allowed&state={state or ''}"
        )
    
    # Check if the user is authenticated
    if not current_user:
        # Redirect to login page with return_to parameter
        return RedirectResponse(
            f"/auth/login?return_to=/oidc/authorize?{request.query_params}"
        )
    
    # Check if PKCE is required but not provided
    if client.require_pkce and not (code_challenge and code_challenge_method):
        return RedirectResponse(
            f"{redirect_uri}?error=invalid_request&error_description=PKCE+required&state={state or ''}"
        )
    
    # Check if the user has consented to the requested scopes
    has_consent = await ensure_user_consent(db, current_user.id, client_id, requested_scopes)
    
    if not has_consent and prompt != "none":
        # Redirect to consent page
        return RedirectResponse(
            f"/oidc/consent?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&state={state or ''}&response_type={response_type}&nonce={nonce or ''}&code_challenge={code_challenge or ''}&code_challenge_method={code_challenge_method or ''}"
        )
    elif not has_consent and prompt == "none":
        # If prompt=none and consent is required, return an error
        return RedirectResponse(
            f"{redirect_uri}?error=consent_required&error_description=User+consent+required&state={state or ''}"
        )
    
    # Process the authorization request based on response_type
    if response_type == "code":
        # Authorization Code Flow
        code = await create_authorization_code_flow(
            db,
            client_id=client_id,
            user_id=current_user.id,
            redirect_uri=redirect_uri,
            scope=scope,
            nonce=nonce,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
        )
        
        # Redirect to the redirect URI with the authorization code
        return RedirectResponse(
            f"{redirect_uri}?code={code}&state={state or ''}"
        )
    
    elif response_type == "token":
        # Implicit Flow - Access Token only
        from usery.services.security import create_access_token
        
        access_token = create_access_token(
            current_user.id,
            expires_delta=timedelta(seconds=client.access_token_timeout)
        )
        
        # Redirect to the redirect URI with the access token
        return RedirectResponse(
            f"{redirect_uri}#access_token={access_token}&token_type=bearer&expires_in={client.access_token_timeout}&state={state or ''}&scope={scope}"
        )
    
    elif response_type == "id_token":
        # Implicit Flow - ID Token only
        id_token = await create_id_token(
            db,
            client,
            current_user,
            nonce=nonce,
            expires_in=client.access_token_timeout
        )
        
        # Redirect to the redirect URI with the ID token
        return RedirectResponse(
            f"{redirect_uri}#id_token={id_token}&state={state or ''}"
        )
    
    elif response_type == "code token":
        # Hybrid Flow - Authorization Code and Access Token
        code = await create_authorization_code_flow(
            db,
            client_id=client_id,
            user_id=current_user.id,
            redirect_uri=redirect_uri,
            scope=scope,
            nonce=nonce,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
        )
        
        from usery.services.security import create_access_token
        
        access_token = create_access_token(
            current_user.id,
            expires_delta=timedelta(seconds=client.access_token_timeout)
        )
        
        # Redirect to the redirect URI with the authorization code and access token
        return RedirectResponse(
            f"{redirect_uri}#code={code}&access_token={access_token}&token_type=bearer&expires_in={client.access_token_timeout}&state={state or ''}&scope={scope}"
        )
    
    elif response_type == "code id_token":
        # Hybrid Flow - Authorization Code and ID Token
        code = await create_authorization_code_flow(
            db,
            client_id=client_id,
            user_id=current_user.id,
            redirect_uri=redirect_uri,
            scope=scope,
            nonce=nonce,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
        )
        
        id_token = await create_id_token(
            db,
            client,
            current_user,
            nonce=nonce,
            code=code,
            expires_in=client.access_token_timeout
        )
        
        # Redirect to the redirect URI with the authorization code and ID token
        return RedirectResponse(
            f"{redirect_uri}#code={code}&id_token={id_token}&state={state or ''}"
        )
    
    elif response_type == "token id_token":
        # Implicit Flow - Access Token and ID Token
        from usery.services.security import create_access_token
        
        access_token = create_access_token(
            current_user.id,
            expires_delta=timedelta(seconds=client.access_token_timeout)
        )
        
        id_token = await create_id_token(
            db,
            client,
            current_user,
            nonce=nonce,
            access_token=access_token,
            expires_in=client.access_token_timeout
        )
        
        # Redirect to the redirect URI with the access token and ID token
        return RedirectResponse(
            f"{redirect_uri}#access_token={access_token}&token_type=bearer&id_token={id_token}&expires_in={client.access_token_timeout}&state={state or ''}&scope={scope}"
        )
    
    elif response_type == "code token id_token":
        # Hybrid Flow - Authorization Code, Access Token, and ID Token
        code = await create_authorization_code_flow(
            db,
            client_id=client_id,
            user_id=current_user.id,
            redirect_uri=redirect_uri,
            scope=scope,
            nonce=nonce,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
        )
        
        from usery.services.security import create_access_token
        
        access_token = create_access_token(
            current_user.id,
            expires_delta=timedelta(seconds=client.access_token_timeout)
        )
        
        id_token = await create_id_token(
            db,
            client,
            current_user,
            nonce=nonce,
            access_token=access_token,
            code=code,
            expires_in=client.access_token_timeout
        )
        
        # Redirect to the redirect URI with the authorization code, access token, and ID token
        return RedirectResponse(
            f"{redirect_uri}#code={code}&access_token={access_token}&token_type=bearer&id_token={id_token}&expires_in={client.access_token_timeout}&state={state or ''}&scope={scope}"
        )
    
    else:
        # Unsupported response type
        return RedirectResponse(
            f"{redirect_uri}?error=unsupported_response_type&error_description=Response+type+not+supported&state={state or ''}"
        )


@router.get("/consent", response_class=HTMLResponse)
async def consent_page(
    client_id: UUID,
    redirect_uri: str,
    scope: str,
    response_type: str,
    state: Optional[str] = None,
    nonce: Optional[str] = None,
    code_challenge: Optional[str] = None,
    code_challenge_method: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """
    Consent page for the user to approve the requested scopes.
    """
    # Check if the client exists
    client = await get_client(db, client_id=client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client not found",
        )
    
    # Parse scopes
    requested_scopes = parse_scopes(scope)
    
    # Generate a simple HTML consent page
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Consent Required</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; }}
            h1 {{ color: #333; }}
            .scope {{ margin: 10px 0; padding: 10px; background-color: #f5f5f5; border-radius: 5px; }}
            .buttons {{ margin-top: 20px; }}
            .btn {{ padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; margin-right: 10px; }}
            .btn-primary {{ background-color: #007bff; color: white; }}
            .btn-secondary {{ background-color: #6c757d; color: white; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Consent Required</h1>
            <p>The application <strong>{client.title}</strong> is requesting access to your account.</p>
            
            <h2>Requested Permissions:</h2>
            <div class="scopes">
    """
    
    # Add each scope with a description
    scope_descriptions = {
        "openid": "Verify your identity",
        "profile": "Access your profile information",
        "email": "Access your email address",
        "offline_access": "Access your data when you're not present (via refresh token)",
    }
    
    for scope_name in requested_scopes:
        description = scope_descriptions.get(scope_name, scope_name)
        html_content += f'<div class="scope"><strong>{scope_name}</strong>: {description}</div>'
    
    # Add form buttons
    html_content += f"""
            </div>
            
            <div class="buttons">
                <form method="post" action="/oidc/consent">
                    <input type="hidden" name="client_id" value="{client_id}">
                    <input type="hidden" name="redirect_uri" value="{redirect_uri}">
                    <input type="hidden" name="scope" value="{scope}">
                    <input type="hidden" name="response_type" value="{response_type}">
                    <input type="hidden" name="state" value="{state or ''}">
                    <input type="hidden" name="nonce" value="{nonce or ''}">
                    <input type="hidden" name="code_challenge" value="{code_challenge or ''}">
                    <input type="hidden" name="code_challenge_method" value="{code_challenge_method or ''}">
                    <input type="hidden" name="approved" value="true">
                    <button type="submit" class="btn btn-primary">Allow</button>
                </form>
                
                <form method="post" action="/oidc/consent" style="display: inline;">
                    <input type="hidden" name="client_id" value="{client_id}">
                    <input type="hidden" name="redirect_uri" value="{redirect_uri}">
                    <input type="hidden" name="state" value="{state or ''}">
                    <input type="hidden" name="approved" value="false">
                    <button type="submit" class="btn btn-secondary">Deny</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content


@router.post("/consent")
async def process_consent(
    client_id: UUID = Form(...),
    redirect_uri: str = Form(...),
    approved: str = Form(...),
    scope: Optional[str] = Form(None),
    response_type: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    nonce: Optional[str] = Form(None),
    code_challenge: Optional[str] = Form(None),
    code_challenge_method: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """
    Process the user's consent decision.
    """
    # Check if the client exists
    client = await get_client(db, client_id=client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client not found",
        )
    
    # Check if the redirect URI is allowed
    if redirect_uri not in client.redirect_uris:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Redirect URI not allowed",
        )
    
    if approved.lower() == "true":
        # User approved the consent
        # Record the user's consent
        requested_scopes = parse_scopes(scope)
        await record_user_consent(db, current_user.id, client_id, requested_scopes)
        
        # Redirect back to the authorization endpoint to complete the flow
        return RedirectResponse(
            f"/oidc/authorize?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&response_type={response_type}&state={state or ''}&nonce={nonce or ''}&code_challenge={code_challenge or ''}&code_challenge_method={code_challenge_method or ''}",
            status_code=status.HTTP_303_SEE_OTHER
        )
    else:
        # User denied the consent
        return RedirectResponse(
            f"{redirect_uri}?error=access_denied&error_description=The+user+denied+the+request&state={state or ''}",
            status_code=status.HTTP_303_SEE_OTHER
        )


@router.post("/token")
async def token(
    grant_type: str = Form(...),
    client_id: UUID = Form(...),
    client_secret: Optional[str] = Form(None),
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    code_verifier: Optional[str] = Form(None),
    refresh_token: Optional[str] = Form(None),
    scope: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Token endpoint.
    
    This endpoint is used to obtain tokens.
    """
    # Check if the client exists
    client = await get_client(db, client_id=client_id)
    if not client:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "invalid_client", "error_description": "Client not found"}
        )
    
    # Verify client authentication
    if client.client_type == "confidential" and client.token_endpoint_auth_method != "none":
        if not client_secret or client_secret != client.client_secret:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "invalid_client", "error_description": "Invalid client credentials"}
            )
    
    # Process the token request based on grant_type
    if grant_type == "authorization_code":
        # Authorization Code Flow
        if not code or not redirect_uri:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "invalid_request", "error_description": "Code and redirect_uri are required"}
            )
        
        # Exchange the authorization code for tokens
        access_token, refresh_token, id_token, expires_in, token_scope = await exchange_authorization_code(
            db,
            code=code,
            client_id=client_id,
            redirect_uri=redirect_uri,
            code_verifier=code_verifier
        )
        
        if not access_token:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "invalid_grant", "error_description": "Invalid authorization code"}
            )
        
        # Build the response
        response = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "scope": token_scope,
        }
        
        if refresh_token:
            response["refresh_token"] = refresh_token
        
        if id_token:
            response["id_token"] = id_token
        
        return response
    
    elif grant_type == "refresh_token":
        # Refresh Token Flow
        if not refresh_token:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "invalid_request", "error_description": "Refresh token is required"}
            )
        
        # Refresh the tokens
        access_token, new_refresh_token, id_token, expires_in, token_scope = await refresh_tokens(
            db,
            refresh_token=refresh_token,
            client_id=client_id,
            scope=scope
        )
        
        if not access_token:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "invalid_grant", "error_description": "Invalid refresh token"}
            )
        
        # Build the response
        response = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "scope": token_scope,
        }
        
        if new_refresh_token:
            response["refresh_token"] = new_refresh_token
        
        if id_token:
            response["id_token"] = id_token
        
        return response
    
    elif grant_type == "client_credentials":
        # Client Credentials Flow
        # This flow is for client-to-client authentication without a user
        # It's typically used for server-to-server API access
        
        # Verify that the client is allowed to use this grant type
        if "client_credentials" not in client.grant_types:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "unauthorized_client", "error_description": "Client not authorized for client_credentials grant"}
            )
        
        # Create an access token for the client
        from usery.services.security import create_access_token
        
        access_token = create_access_token(
            client_id,  # Use client_id as the subject
            expires_delta=timedelta(seconds=client.access_token_timeout)
        )
        
        # Determine the scope
        if scope:
            requested_scopes = parse_scopes(scope)
            allowed_scopes = set(client.allowed_scopes)
            
            if not requested_scopes.issubset(allowed_scopes):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "invalid_scope", "error_description": "Scope not allowed"}
                )
            
            token_scope = scope
        else:
            token_scope = join_scopes(set(client.allowed_scopes))
        
        # Build the response
        response = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": client.access_token_timeout,
            "scope": token_scope,
        }
        
        return response
    
    else:
        # Unsupported grant type
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "unsupported_grant_type", "error_description": "Grant type not supported"}
        )


@router.get("/userinfo")
async def userinfo(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """
    UserInfo endpoint.
    
    This endpoint returns claims about the authenticated user.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    # Build the response with standard claims
    response = {
        "sub": str(current_user.id),  # Subject identifier
        "name": current_user.full_name,
        "preferred_username": current_user.username,
        "email": current_user.email,
        "email_verified": current_user.is_verified,
    }
    
    return response


@router.post("/revoke")
async def revoke_token(
    token: str = Form(...),
    token_type_hint: Optional[str] = Form(None),
    client_id: UUID = Form(...),
    client_secret: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Token Revocation endpoint.
    
    This endpoint allows clients to notify the authorization server that a
    previously obtained refresh or access token is no longer needed.
    """
    # Check if the client exists
    client = await get_client(db, client_id=client_id)
    if not client:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "invalid_client", "error_description": "Client not found"}
        )
    
    # Verify client authentication
    if client.client_type == "confidential" and client.token_endpoint_auth_method != "none":
        if not client_secret or client_secret != client.client_secret:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "invalid_client", "error_description": "Invalid client credentials"}
            )
    
    # Determine the token type
    if token_type_hint == "refresh_token" or (not token_type_hint and len(token) > 40):
        # Try to revoke as refresh token
        from usery.services.refresh_token import revoke_refresh_token
        await revoke_refresh_token(db, token)
    else:
        # For access tokens, add to the blacklist
        from usery.services.security import store_token_in_blacklist
        from usery.db.redis import get_redis
        
        redis_client = await get_redis()
        await store_token_in_blacklist(
            redis_client, 
            token, 
            settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    # The spec requires a 200 OK response with an empty body
    return Response(status_code=status.HTTP_200_OK)


@router.get("/end_session")
async def end_session(
    id_token_hint: Optional[str] = None,
    post_logout_redirect_uri: Optional[str] = None,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user),
) -> Any:
    """
    End Session endpoint.
    
    This endpoint logs the user out and optionally redirects to a specified URI.
    """
    # If the user is logged in, log them out
    if current_user:
        # Revoke all refresh tokens for the user
        from usery.services.refresh_token import revoke_user_tokens
        await revoke_user_tokens(db, current_user.id)
        
        # Invalidate the session
        # This would typically be handled by your session management system
        # For this example, we'll just redirect to the logout endpoint
        
    # If a post-logout redirect URI is provided and it's valid, redirect to it
    if post_logout_redirect_uri:
        # In a real implementation, you would verify that the URI is allowed
        # for the client associated with the id_token_hint
        
        redirect_url = post_logout_redirect_uri
        if state:
            redirect_url += f"?state={state}"
        
        return RedirectResponse(redirect_url)
    
    # Otherwise, show a simple logout confirmation page
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Logged Out</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                .container { max-width: 600px; margin: 0 auto; text-align: center; }
                h1 { color: #333; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>You have been logged out</h1>
                <p>You have been successfully logged out of the system.</p>
            </div>
        </body>
        </html>
        """
    )