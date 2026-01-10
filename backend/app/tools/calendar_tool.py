"""
Google Calendar Tool
Integrates with Google Calendar API for event management.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.tools.base_tool import BaseTool, ToolSchema, ToolParameter
from app.services.google_oauth import get_credentials_for_user

logger = logging.getLogger(__name__)


class CalendarTool(BaseTool):
    """Tool for interacting with Google Calendar."""
    
    @property
    def name(self) -> str:
        return "calendar"
    
    @property
    def description(self) -> str:
        return "Create, read, update, and delete events in Google Calendar"
    
    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="Action to perform: 'create', 'list', 'update', 'delete'",
                    required=True
                ),
                ToolParameter(
                    name="summary",
                    type="string",
                    description="Event title/summary (for create/update)",
                    required=False
                ),
                ToolParameter(
                    name="description",
                    type="string",
                    description="Event description (for create/update)",
                    required=False
                ),
                ToolParameter(
                    name="start_time",
                    type="string",
                    description="Event start time in ISO format (for create/update)",
                    required=False
                ),
                ToolParameter(
                    name="end_time",
                    type="string",
                    description="Event end time in ISO format (for create/update)",
                    required=False
                ),
                ToolParameter(
                    name="event_id",
                    type="string",
                    description="Event ID (for update/delete)",
                    required=False
                ),
                ToolParameter(
                    name="max_results",
                    type="integer",
                    description="Maximum number of events to return (for list)",
                    required=False,
                    default=10
                ),
                ToolParameter(
                    name="time_min",
                    type="string",
                    description="Minimum time to filter events (ISO format, for list)",
                    required=False
                ),
                ToolParameter(
                    name="time_max",
                    type="string",
                    description="Maximum time to filter events (ISO format, for list)",
                    required=False
                ),
                ToolParameter(
                    name="attendees",
                    type="array",
                    description="List of attendee emails (for create/update)",
                    required=False
                ),
                ToolParameter(
                    name="location",
                    type="string",
                    description="Event location (for create/update)",
                    required=False
                )
            ]
        )
    
    async def execute(self, params: Dict[str, Any], user_id: str = "default_user") -> Dict[str, Any]:
        """Execute calendar operation."""
        try:
            self.validate_params(params)
            
            action = params.get("action")
            
            # Get user credentials
            credentials = get_credentials_for_user(user_id)
            if not credentials:
                return {
                    "success": False,
                    "error": "User not authenticated with Google Calendar. Please connect your Google account."
                }
            
            # Build Calendar service
            service = build('calendar', 'v3', credentials=credentials)
            
            # Route to appropriate action
            if action == "create":
                return await self._create_event(service, params)
            elif action == "list":
                return await self._list_events(service, params)
            elif action == "update":
                return await self._update_event(service, params)
            elif action == "delete":
                return await self._delete_event(service, params)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
                
        except Exception as e:
            logger.error(f"❌ Calendar tool error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _create_event(self, service, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new calendar event."""
        try:
            event = {
                'summary': params.get('summary', 'Untitled Event'),
                'description': params.get('description', ''),
                'start': {
                    'dateTime': params.get('start_time'),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': params.get('end_time'),
                    'timeZone': 'UTC',
                },
            }
            
            # Add optional fields
            if params.get('location'):
                event['location'] = params['location']
            
            if params.get('attendees'):
                event['attendees'] = [{'email': email} for email in params['attendees']]
            
            # Create event
            created_event = service.events().insert(calendarId='primary', body=event).execute()
            
            logger.info(f"✅ Created calendar event: {created_event['id']}")
            
            return {
                "success": True,
                "event_id": created_event['id'],
                "html_link": created_event.get('htmlLink'),
                "summary": created_event.get('summary'),
                "start": created_event['start'].get('dateTime'),
                "end": created_event['end'].get('dateTime')
            }
            
        except HttpError as e:
            logger.error(f"❌ HTTP error creating event: {e}")
            return {
                "success": False,
                "error": f"Calendar API error: {e.reason}"
            }
    
    async def _list_events(self, service, params: Dict[str, Any]) -> Dict[str, Any]:
        """List calendar events."""
        try:
            max_results = params.get('max_results', 10)
            time_min = params.get('time_min', datetime.utcnow().isoformat() + 'Z')
            time_max = params.get('time_max', None)
            
            # Build request parameters
            list_params = {
                'calendarId': 'primary',
                'timeMin': time_min,
                'maxResults': max_results,
                'singleEvents': True,
                'orderBy': 'startTime'
            }
            
            # Add timeMax if filtering by specific date range
            if time_max:
                list_params['timeMax'] = time_max
            
            events_result = service.events().list(**list_params).execute()
            
            events = events_result.get('items', [])
            
            logger.info(f"✅ Listed {len(events)} calendar events")
            
            formatted_events = []
            for event in events:
                formatted_events.append({
                    'id': event['id'],
                    'summary': event.get('summary', 'No title'),
                    'start': event['start'].get('dateTime', event['start'].get('date')),
                    'end': event['end'].get('dateTime', event['end'].get('date')),
                    'description': event.get('description', ''),
                    'location': event.get('location', ''),
                    'html_link': event.get('htmlLink')
                })
            
            return {
                "success": True,
                "events": formatted_events,
                "count": len(formatted_events)
            }
            
        except HttpError as e:
            logger.error(f"❌ HTTP error listing events: {e}")
            return {
                "success": False,
                "error": f"Calendar API error: {e.reason}"
            }
    
    async def _update_event(self, service, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing calendar event."""
        try:
            event_id = params.get('event_id')
            if not event_id:
                return {"success": False, "error": "event_id is required for update"}
            
            # Get existing event
            event = service.events().get(calendarId='primary', eventId=event_id).execute()
            
            # Update fields
            if params.get('summary'):
                event['summary'] = params['summary']
            if params.get('description'):
                event['description'] = params['description']
            if params.get('start_time'):
                event['start'] = {'dateTime': params['start_time'], 'timeZone': 'UTC'}
            if params.get('end_time'):
                event['end'] = {'dateTime': params['end_time'], 'timeZone': 'UTC'}
            if params.get('location'):
                event['location'] = params['location']
            
            # Update event
            updated_event = service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            
            logger.info(f"✅ Updated calendar event: {event_id}")
            
            return {
                "success": True,
                "event_id": updated_event['id'],
                "summary": updated_event.get('summary'),
                "html_link": updated_event.get('htmlLink')
            }
            
        except HttpError as e:
            logger.error(f"❌ HTTP error updating event: {e}")
            return {
                "success": False,
                "error": f"Calendar API error: {e.reason}"
            }
    
    async def _delete_event(self, service, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a calendar event."""
        try:
            event_id = params.get('event_id')
            if not event_id:
                return {"success": False, "error": "event_id is required for delete"}
            
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            
            logger.info(f"✅ Deleted calendar event: {event_id}")
            
            return {
                "success": True,
                "message": f"Event {event_id} deleted successfully"
            }
            
        except HttpError as e:
            logger.error(f"❌ HTTP error deleting event: {e}")
            return {
                "success": False,
                "error": f"Calendar API error: {e.reason}"
            }


# Singleton instance
_calendar_tool: Optional[CalendarTool] = None


def get_calendar_tool() -> CalendarTool:
    """Get or create CalendarTool singleton."""
    global _calendar_tool
    if _calendar_tool is None:
        _calendar_tool = CalendarTool()
    return _calendar_tool
