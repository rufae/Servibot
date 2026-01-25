"""
Google Contacts API endpoints
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

from app.auth.jwt_handler import verify_token
from app.db.sqlite_client import get_sqlite_client
from app.tools.contacts_tool import get_contacts_tool

logger = logging.getLogger(__name__)
router = APIRouter()


class ContactSearchRequest(BaseModel):
    """Contact search request model."""
    query: str


@router.get("/contacts")
async def get_contacts(
    page_size: int = 100,
    page_token: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """
    Get user's Google contacts.
    Requires Google account to be connected.
    """
    try:
        # Verify authentication
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization required")
        
        token = authorization.replace('Bearer ', '')
        user_id = verify_token(token)
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get contacts
        contacts_tool = get_contacts_tool()
        result = await contacts_tool.execute({
            "action": "list",
            "page_size": page_size,
            "page_token": page_token
        }, user_id=str(user_id))
        
        if not result.get("success"):
            if result.get("requires_auth"):
                raise HTTPException(status_code=403, detail=result.get("error"))
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return {
            "success": True,
            "contacts": result.get("contacts", []),
            "total": result.get("total", 0),
            "next_page_token": result.get("next_page_token")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contacts/search")
async def search_contacts(
    request: ContactSearchRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Search contacts by name.
    """
    try:
        # Verify authentication
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization required")
        
        token = authorization.replace('Bearer ', '')
        user_id = verify_token(token)
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Search contacts
        contacts_tool = get_contacts_tool()
        result = await contacts_tool.execute({
            "action": "search",
            "query": request.query
        }, user_id=str(user_id))
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return {
            "success": True,
            "contacts": result.get("contacts", []),
            "total": result.get("total", 0),
            "query": request.query
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contacts/{resource_name:path}")
async def get_contact_detail(
    resource_name: str,
    authorization: Optional[str] = Header(None)
):
    """
    Get detailed information about a specific contact.
    """
    try:
        # Verify authentication
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization required")
        
        token = authorization.replace('Bearer ', '')
        user_id = verify_token(token)
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get contact
        contacts_tool = get_contacts_tool()
        result = await contacts_tool.execute({
            "action": "get",
            "resource_name": resource_name
        }, user_id=str(user_id))
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))
        
        return {
            "success": True,
            "contact": result.get("contact")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contact detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))
