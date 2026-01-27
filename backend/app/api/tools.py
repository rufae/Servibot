"""
Tools API Endpoints
HTTP endpoints to use Calendar and Gmail tools directly.
"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel

from app.tools.calendar_tool import get_calendar_tool
from app.tools.email_tool import get_email_tool
from fastapi import Header
from app.auth.jwt_handler import verify_token
from app.db.sqlite_client import get_sqlite_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tools", tags=["Tools"])


# Request models
class CalendarEventRequest(BaseModel):
    """Request model for calendar operations."""
    action: str
    summary: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    event_id: Optional[str] = None
    max_results: Optional[int] = 10
    time_min: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[list] = None


class EmailRequest(BaseModel):
    """Request model for email operations."""
    action: str
    to: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    message_id: Optional[str] = None
    query: Optional[str] = None
    max_results: Optional[int] = 10
    cc: Optional[str] = None
    bcc: Optional[str] = None


# Calendar endpoints
@router.get("/calendar/events")
async def list_calendar_events(
    user_id: str = Query(default="default_user"),
    max_results: int = Query(default=10),
    authorization: Optional[str] = Header(None)
):
    """List upcoming calendar events."""
    try:
        # Prefer authenticated user from Authorization header
        if authorization:
            try:
                token = authorization.replace('Bearer ', '') if 'Bearer ' in authorization else authorization
                uid = verify_token(token)
                if uid:
                    db = get_sqlite_client()
                    user = db.get_user_by_id(int(uid))
                    if user:
                        user_id = str(user.get('id'))
                        logger.info(f"✅ Using user_id: {user_id} for tools endpoint")
            except Exception:
                logger.warning("Could not extract user from Authorization header for tools endpoint")

        calendar_tool = get_calendar_tool()
        result = await calendar_tool.execute({
            "action": "list",
            "max_results": max_results
        }, user_id=user_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to list events"))
        
        return result
    except Exception as e:
        logger.error(f"Error listing calendar events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calendar/events")
async def create_calendar_event(
    request: CalendarEventRequest,
    user_id: str = Query(default="default_user"),
    authorization: Optional[str] = Header(None)
):
    """Create a new calendar event."""
    try:
        if authorization:
            try:
                token = authorization.replace('Bearer ', '') if 'Bearer ' in authorization else authorization
                uid = verify_token(token)
                if uid:
                    db = get_sqlite_client()
                    user = db.get_user_by_id(int(uid))
                    if user:
                        user_id = str(user.get('id'))
                        logger.info(f"✅ Using user_id: {user_id} for tools endpoint")
            except Exception:
                logger.warning("Could not extract user from Authorization header for tools endpoint")

        calendar_tool = get_calendar_tool()
        result = await calendar_tool.execute({
            "action": "create",
            "summary": request.summary,
            "description": request.description,
            "start_time": request.start_time,
            "end_time": request.end_time,
            "location": request.location,
            "attendees": request.attendees
        }, user_id=user_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to create event"))
        
        return result
    except Exception as e:
        logger.error(f"Error creating calendar event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calendar")
async def calendar_action(
    request: CalendarEventRequest,
    user_id: str = Query(default="default_user"),
    authorization: Optional[str] = Header(None)
):
    """Execute any calendar action (create, list, update, delete)."""
    try:
        if authorization:
            try:
                token = authorization.replace('Bearer ', '') if 'Bearer ' in authorization else authorization
                uid = verify_token(token)
                if uid:
                    db = get_sqlite_client()
                    user = db.get_user_by_id(int(uid))
                    if user:
                        user_id = str(user.get('id'))
                        logger.info(f"✅ Using user_id: {user_id} for tools endpoint")
            except Exception:
                logger.warning("Could not extract user from Authorization header for tools endpoint")

        calendar_tool = get_calendar_tool()
        result = await calendar_tool.execute(request.dict(exclude_none=True), user_id=user_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Calendar action failed"))
        
        return result
    except Exception as e:
        logger.error(f"Error executing calendar action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Gmail endpoints
@router.get("/gmail/messages")
async def list_emails(
    user_id: str = Query(default="default_user"),
    max_results: int = Query(default=10),
    query: Optional[str] = Query(None),
    page_token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    """List recent emails or search emails with pagination support."""
    try:
        if authorization:
            try:
                token = authorization.replace('Bearer ', '') if 'Bearer ' in authorization else authorization
                uid = verify_token(token)
                if uid:
                    db = get_sqlite_client()
                    user = db.get_user_by_id(int(uid))
                    if user:
                        user_id = str(user.get('id'))
                        logger.info(f"✅ Using user_id: {user_id} for tools endpoint")
            except Exception:
                logger.warning("Could not extract user from Authorization header for tools endpoint")

        email_tool = get_email_tool()
        
        params = {
            "action": "search" if query else "list",
            "max_results": max_results
        }
        
        if query:
            params["query"] = query
        if page_token:
            params["page_token"] = page_token
        
        result = await email_tool.execute(params, user_id=user_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to list emails"))
        
        return result
    except Exception as e:
        logger.error(f"Error listing emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gmail/send")
async def send_email(
    request: EmailRequest,
    user_id: str = Query(default="default_user"),
    authorization: Optional[str] = Header(None)
):
    """Send an email."""
    try:
        if authorization:
            try:
                token = authorization.replace('Bearer ', '') if 'Bearer ' in authorization else authorization
                uid = verify_token(token)
                if uid:
                    db = get_sqlite_client()
                    user = db.get_user_by_id(int(uid))
                    if user:
                        user_id = str(user.get('id'))
                        logger.info(f"✅ Using user_id: {user_id} for tools endpoint")
            except Exception:
                logger.warning("Could not extract user from Authorization header for tools endpoint")

        email_tool = get_email_tool()
        result = await email_tool.execute({
            "action": "send",
            "to": request.to,
            "subject": request.subject,
            "body": request.body,
            "cc": request.cc,
            "bcc": request.bcc
        }, user_id=user_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to send email"))
        
        return result
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gmail")
async def gmail_action(
    request: EmailRequest,
    user_id: str = Query(default="default_user"),
    authorization: Optional[str] = Header(None)
):
    """Execute any email action (send, list, read, search, delete)."""
    try:
        if authorization:
            try:
                token = authorization.replace('Bearer ', '') if 'Bearer ' in authorization else authorization
                uid = verify_token(token)
                if uid:
                    db = get_sqlite_client()
                    user = db.get_user_by_id(int(uid))
                    if user:
                        user_id = str(user.get('id'))
                        logger.info(f"✅ Using user_id: {user_id} for tools endpoint")
            except Exception:
                logger.warning("Could not extract user from Authorization header for tools endpoint")

        email_tool = get_email_tool()
        result = await email_tool.execute(request.dict(exclude_none=True), user_id=user_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Email action failed"))
        
        return result
    except Exception as e:
        logger.error(f"Error executing email action: {e}")
        raise HTTPException(status_code=500, detail=str(e))
