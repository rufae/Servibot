"""
Google OAuth Authentication Endpoints
Handles OAuth flow for Google Calendar and Gmail integration.
"""
import logging
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from datetime import timedelta

from app.services.google_oauth import (
    build_oauth_flow,
    get_authorization_url,
    exchange_code_for_credentials,
    save_credentials_for_user
)
from app.auth.jwt_handler import create_access_token
from app.db.sqlite_client import get_sqlite_client
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/google", tags=["Google OAuth"])


class OAuthStartResponse(BaseModel):
    """Response model for OAuth start."""
    authorization_url: str
    state: str


@router.get("/start")
async def start_oauth(
    user_id: str = Query(default="default_user", description="User identifier")
):
    """
    Start Google OAuth flow.
    
    This endpoint redirects the user to Google's authorization page.
    
    Args:
        user_id: User identifier to associate with the token
    
    Returns:
        Redirect to Google OAuth consent screen
    """
    try:
        flow = build_oauth_flow()
        
        # Include user_id in state for callback
        state = f"user_id={user_id}"
        
        auth_url, state = get_authorization_url(flow, state=state)
        
        logger.info(f"🚀 Starting OAuth flow for user {user_id}")
        
        # Redirect to Google authorization page
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        logger.error(f"❌ Error starting OAuth flow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start OAuth flow: {str(e)}")


@router.get("/callback")
async def oauth_callback(
    code: Optional[str] = Query(None, description="Authorization code from Google"),
    state: Optional[str] = Query(None, description="State parameter"),
    error: Optional[str] = Query(None, description="Error from OAuth provider")
):
    """
    Handle Google OAuth callback.
    
    This endpoint receives the authorization code from Google,
    exchanges it for tokens, and stores them.
    
    Args:
        code: Authorization code from Google
        state: State parameter containing user_id
        error: Error message if authorization failed
    
    Returns:
        Redirect to frontend with success or error
    """
    # Handle OAuth errors
    if error:
        logger.error(f"❌ OAuth error: {error}")
        error_url = f"{settings.FRONTEND_URL}?oauth_error={error}"
        return RedirectResponse(url=error_url)
    
    if not code:
        logger.error("❌ No authorization code received")
        error_url = f"{settings.FRONTEND_URL}?oauth_error=no_code"
        return RedirectResponse(url=error_url)
    
    try:
        # Extract user_id from state
        user_id = "default_user"
        if state and "user_id=" in state:
            user_id = state.split("user_id=")[1].split("&")[0]
        
        logger.info(f"🔄 Processing OAuth callback for user {user_id}")
        
        # Exchange code for credentials
        flow = build_oauth_flow()
        credentials = exchange_code_for_credentials(flow, code)
        
        # Extract Google user ID from id_token if available
        sub = None
        email = None
        name = None
        picture = None
        
        if hasattr(credentials, 'id_token') and credentials.id_token:
            import jwt
            decoded = jwt.decode(credentials.id_token, options={"verify_signature": False})
            sub = decoded.get('sub')
            email = decoded.get('email')
            name = decoded.get('name')
            picture = decoded.get('picture')
            logger.info(f"✅ Google user ID (sub): {sub}, email: {email}")
        
        # Create or update user in database
        db = get_sqlite_client()
        user_data = db.create_or_update_user(
            google_id=sub,
            email=email,
            name=name,
            picture=picture
        )
        
        # Save credentials to database (now associated with user DB id)
        token_id = save_credentials_for_user(credentials, str(user_data['id']), sub)
        
        # Create JWT session token
        access_token = create_access_token(
            data={
                "sub": str(user_data['id']),
                "email": email,
                "name": name,
                "picture": picture,
                "google_id": sub
            },
            expires_delta=timedelta(days=7)
        )
        
        logger.info(f"✅ OAuth successful for user {email} (user_id={user_data['id']})")
        
        # Redirect to frontend with token
        success_url = f"{settings.FRONTEND_URL}/auth/callback?token={access_token}"
        return RedirectResponse(url=success_url)
        
    except Exception as e:
        logger.error(f"❌ Error in OAuth callback: {e}", exc_info=True)
        error_url = f"{settings.FRONTEND_URL}?oauth_error={str(e)}"
        return RedirectResponse(url=error_url)


@router.get("/status")
async def check_oauth_status(
    user_id: str = Query(default="default_user", description="User identifier")
):
    """
    Check if user has valid OAuth credentials.
    
    Args:
        user_id: User identifier
    
    Returns:
        Status of OAuth connection
    """
    from app.services.google_oauth import get_credentials_for_user
    
    credentials = get_credentials_for_user(user_id)
    
    if credentials:
        return {
            "connected": True,
            "user_id": user_id,
            "scopes": credentials.scopes
        }
    else:
        return {
            "connected": False,
            "user_id": user_id
        }


@router.post("/revoke")
async def revoke_oauth(
    user_id: str = Query(default="default_user", description="User identifier")
):
    """
    Revoke OAuth credentials for a user.
    
    Args:
        user_id: User identifier
    
    Returns:
        Success message
    """
    from app.services.google_oauth import revoke_credentials_for_user
    
    success = revoke_credentials_for_user(user_id)
    
    if success:
        logger.info(f"✅ Revoked OAuth for user {user_id}")
        return {"message": "OAuth credentials revoked successfully"}
    else:
        raise HTTPException(status_code=404, detail="No credentials found for user")

