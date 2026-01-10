"""
Google OAuth Service
Handles OAuth flow and credential management for Google APIs.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

from app.core.config import settings
from app.db.sqlite_client import get_sqlite_client

logger = logging.getLogger(__name__)


def build_oauth_flow(redirect_uri: Optional[str] = None) -> Flow:
    """
    Build Google OAuth flow.
    
    Args:
        redirect_uri: Optional custom redirect URI
    
    Returns:
        Configured Flow object
    """
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri or settings.GOOGLE_OAUTH_REDIRECT_URI]
        }
    }
    
    scopes = settings.GOOGLE_OAUTH_SCOPES.split(',')
    
    flow = Flow.from_client_config(
        client_config,
        scopes=scopes,
        redirect_uri=redirect_uri or settings.GOOGLE_OAUTH_REDIRECT_URI
    )
    
    return flow


def get_authorization_url(
    flow: Flow,
    state: Optional[str] = None
) -> tuple[str, str]:
    """
    Get authorization URL for OAuth flow.
    
    Args:
        flow: OAuth flow object
        state: Optional state parameter
    
    Returns:
        Tuple of (authorization_url, state)
    """
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',  # Force refresh token
        state=state
    )
    
    return auth_url, state


def exchange_code_for_credentials(flow: Flow, code: str) -> Credentials:
    """
    Exchange authorization code for credentials.
    
    Args:
        flow: OAuth flow object
        code: Authorization code from callback
    
    Returns:
        Google Credentials object
    """
    flow.fetch_token(code=code)
    return flow.credentials


def credentials_to_dict(credentials: Credentials) -> Dict[str, Any]:
    """
    Convert Credentials object to dictionary for storage.
    
    Args:
        credentials: Google Credentials object
    
    Returns:
        Dictionary representation
    """
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': ','.join(credentials.scopes) if credentials.scopes else '',
        'expiry': int(credentials.expiry.timestamp()) if credentials.expiry else None
    }


def credentials_from_dict(credentials_dict: Dict[str, Any]) -> Credentials:
    """
    Create Credentials object from dictionary.
    
    Args:
        credentials_dict: Dictionary with credential data
    
    Returns:
        Google Credentials object
    """
    expiry = None
    if credentials_dict.get('expiry'):
        expiry = datetime.fromtimestamp(credentials_dict['expiry'])
    
    return Credentials(
        token=credentials_dict.get('token'),
        refresh_token=credentials_dict.get('refresh_token'),
        token_uri=credentials_dict.get('token_uri'),
        client_id=credentials_dict.get('client_id'),
        client_secret=credentials_dict.get('client_secret'),
        scopes=credentials_dict.get('scopes', '').split(',') if credentials_dict.get('scopes') else None,
        expiry=expiry
    )


def get_credentials_for_user(user_id: str) -> Optional[Credentials]:
    """
    Get valid credentials for a user, refreshing if needed.
    
    Args:
        user_id: User identifier
    
    Returns:
        Valid Credentials object or None if not found
    """
    db = get_sqlite_client()
    token_data = db.get_oauth_token('google', user_id=user_id)
    
    if not token_data:
        logger.warning(f"No OAuth token found for user {user_id}")
        return None
    
    credentials = credentials_from_dict(token_data)
    
    # Refresh if expired
    if credentials.expired and credentials.refresh_token:
        logger.info(f"🔄 Refreshing expired token for user {user_id}")
        try:
            credentials.refresh(Request())
            
            # Save updated credentials
            credentials_dict = credentials_to_dict(credentials)
            db.save_oauth_token(
                provider='google',
                credentials_dict=credentials_dict,
                user_id=user_id,
                sub=token_data.get('sub')
            )
            
            logger.info(f"✅ Token refreshed for user {user_id}")
        except Exception as e:
            logger.error(f"❌ Failed to refresh token for user {user_id}: {e}")
            return None
    
    return credentials


def save_credentials_for_user(
    credentials: Credentials,
    user_id: str,
    sub: Optional[str] = None
) -> int:
    """
    Save credentials for a user.
    
    Args:
        credentials: Google Credentials object
        user_id: User identifier
        sub: Optional Google subject ID
    
    Returns:
        Token record ID
    """
    db = get_sqlite_client()
    credentials_dict = credentials_to_dict(credentials)
    
    token_id = db.save_oauth_token(
        provider='google',
        credentials_dict=credentials_dict,
        user_id=user_id,
        sub=sub
    )
    
    return token_id


def revoke_credentials_for_user(user_id: str) -> bool:
    """
    Revoke and delete credentials for a user.
    
    Args:
        user_id: User identifier
    
    Returns:
        True if deleted, False if not found
    """
    db = get_sqlite_client()
    return db.delete_oauth_token('google', user_id=user_id)
