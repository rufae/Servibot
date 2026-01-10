"""
Authentication Middleware
Optional middleware to verify JWT tokens on protected routes.
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from app.auth.jwt_handler import verify_token
from app.db.sqlite_client import get_sqlite_client

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to verify JWT tokens on protected routes.
    
    Protected routes: /api/chat, /api/upload, /api/rag
    Public routes: /auth/*, /docs, /openapi.json, /
    """
    
    # Routes that require authentication
    PROTECTED_PREFIXES = [
        "/api/chat",
        "/api/upload",
        "/api/rag",
        "/api/generate",
        "/api/tools"
    ]
    
    # Routes that are always public
    PUBLIC_PREFIXES = [
        "/auth/",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/"
    ]
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and verify authentication if needed.
        """
        path = request.url.path
        
        # Skip authentication for public routes
        if any(path.startswith(prefix) for prefix in self.PUBLIC_PREFIXES):
            return await call_next(request)
        
        # Check if route requires authentication
        requires_auth = any(path.startswith(prefix) for prefix in self.PROTECTED_PREFIXES)
        
        if not requires_auth:
            return await call_next(request)
        
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            logger.warning(f"⚠️ No authorization header for {path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required. Please login with Google."}
            )
        
        # Extract token
        token = auth_header.replace("Bearer ", "") if "Bearer " in auth_header else auth_header
        
        # Verify token
        user_id = verify_token(token)
        
        if not user_id:
            logger.warning(f"⚠️ Invalid token for {path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token. Please login again."}
            )
        
        # Get user from database
        db = get_sqlite_client()
        user = db.get_user_by_id(int(user_id))
        
        if not user:
            logger.warning(f"⚠️ User not found: {user_id}")
            return JSONResponse(
                status_code=401,
                content={"detail": "User not found. Please login again."}
            )
        
        # Add user to request state for use in endpoints
        request.state.user = user
        request.state.user_id = str(user['id'])
        
        logger.info(f"✅ Authenticated user {user['email']} for {path}")
        
        return await call_next(request)
