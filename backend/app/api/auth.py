"""
Authentication Endpoints
Handles JWT session management.
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from app.auth.jwt_handler import verify_token
from app.db.sqlite_client import get_sqlite_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class UserResponse(BaseModel):
    """User response model."""
    authenticated: bool
    user: Optional[dict] = None


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    authorization: Optional[str] = Header(None)
):
    """
    Get current authenticated user.
    
    Args:
        authorization: Bearer token from Authorization header
    
    Returns:
        User data if authenticated, otherwise error
    """
    if not authorization:
        return UserResponse(authenticated=False)
    
    # Extract token from "Bearer <token>"
    token = authorization.replace("Bearer ", "") if "Bearer " in authorization else authorization
    
    # Verify and decode token
    user_id = verify_token(token)
    if not user_id:
        return UserResponse(authenticated=False)
    
    # Get user from database
    db = get_sqlite_client()
    try:
        user = db.get_user_by_id(int(user_id))
    except Exception as e:
        logger.error(f"❌ Error getting user: {e}")
        return UserResponse(authenticated=False)
    
    if not user:
        return UserResponse(authenticated=False)
    
    return UserResponse(
        authenticated=True,
        user={
            "id": user['id'],
            "email": user['email'],
            "name": user['name'],
            "picture": user['picture']
        }
    )


@router.post("/logout")
async def logout():
    """
    Logout user (client should remove token).
    
    Returns:
        Success message
    """
    logger.info("✅ User logged out")
    return {"success": True, "message": "Logged out successfully"}
