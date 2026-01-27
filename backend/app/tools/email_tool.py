"""
Gmail Tool
Integrates with Gmail API for email management.
"""
import logging
import base64
from typing import Dict, Any, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.tools.base_tool import BaseTool, ToolSchema, ToolParameter
from app.services.google_oauth import get_credentials_for_user
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailTool(BaseTool):
    """Tool for interacting with Gmail."""
    
    @property
    def name(self) -> str:
        return "email"
    
    @property
    def description(self) -> str:
        return "Send, read, search, and manage emails via Gmail"
    
    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="Action to perform: 'send', 'list', 'read', 'search', 'delete'",
                    required=True
                ),
                ToolParameter(
                    name="to",
                    type="string",
                    description="Recipient email address (for send)",
                    required=False
                ),
                ToolParameter(
                    name="subject",
                    type="string",
                    description="Email subject (for send)",
                    required=False
                ),
                ToolParameter(
                    name="body",
                    type="string",
                    description="Email body text (for send)",
                    required=False
                ),
                ToolParameter(
                    name="message_id",
                    type="string",
                    description="Message ID (for read/delete)",
                    required=False
                ),
                ToolParameter(
                    name="query",
                    type="string",
                    description="Search query (for search)",
                    required=False
                ),
                ToolParameter(
                    name="max_results",
                    type="integer",
                    description="Maximum number of messages to return (for list/search)",
                    required=False,
                    default=10
                ),
                ToolParameter(
                    name="cc",
                    type="string",
                    description="CC recipients (comma-separated, for send)",
                    required=False
                ),
                ToolParameter(
                    name="bcc",
                    type="string",
                    description="BCC recipients (comma-separated, for send)",
                    required=False
                )
            ]
        )
    
    async def execute(self, params: Dict[str, Any], user_id: str = "default_user") -> Dict[str, Any]:
        """Execute email operation."""
        try:
            self.validate_params(params)
            
            action = params.get("action")
            
            # Get user credentials
            credentials = get_credentials_for_user(user_id)
            if not credentials:
                # Provide frontend enough info to start OAuth flow
                auth_start = f"/auth/google/start?user_id={user_id}"
                auth_status = f"/auth/google/status?user_id={user_id}"
                return {
                    "success": False,
                    "error": "User not authenticated with Gmail. Please connect your Google account.",
                    "auth_required": True,
                    "auth_url": auth_start,
                    "auth_status_url": auth_status
                }
            
            # Build Gmail service
            service = build('gmail', 'v1', credentials=credentials)
            
            # Route to appropriate action
            if action == "send":
                return await self._send_email(service, params)
            elif action == "list":
                return await self._list_emails(service, params)
            elif action == "read":
                return await self._read_email(service, params)
            elif action == "search":
                return await self._search_emails(service, params)
            elif action == "delete":
                return await self._delete_email(service, params)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
                
        except Exception as e:
            logger.error(f"❌ Email tool error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _send_email(self, service, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send an email."""
        try:
            # Build a multipart/alternative message with plain text and HTML
            message = MIMEMultipart('alternative')
            message['To'] = params.get('to')
            message['Subject'] = params.get('subject', 'No Subject')

            if params.get('cc'):
                message['Cc'] = params['cc']
            if params.get('bcc'):
                message['Bcc'] = params['bcc']

            body = params.get('body', '')

            # Plain text fallback (no greeting or explicit sender signature)
            plain_text = f"""{body}

Support: {settings.FRONTEND_URL}
"""

            # Modern, structured HTML template (no explicit "sent by" signature)
            safe_html_body = (body or '').replace('\n', '<br/>')
            subject_text = params.get('subject', '')
            accent_color = '#3B82F6'  # primary blue accent
            html = f"""
<html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; color: #0f172a; background:#f3f4f6; margin:0; padding:24px;">
        <div style="max-width:700px;margin:0 auto;">
            <!-- Card -->
            <div style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 8px 30px rgba(2,6,23,0.12);">
                <!-- Header bar -->
                <div style="display:flex;align-items:center;gap:12px;padding:16px 20px;background:linear-gradient(90deg,{accent_color}33,{accent_color}22);">
                    <img src="{settings.FRONTEND_URL.rstrip('/')}/Servibot.png" alt="" style="height:36px;object-fit:contain;border-radius:6px;background:transparent;" />
                    <div>
                        <div style="font-size:13px;color:#111;font-weight:700">{subject_text or settings.APP_NAME}</div>
                        <div style="font-size:12px;color:#6b7280;margin-top:2px">{settings.APP_NAME}</div>
                    </div>
                </div>

                <!-- Body -->
                <div style="padding:20px 24px;color:#111;font-size:14px;line-height:1.6;">
                    {safe_html_body}
                </div>

                <!-- Footer with subtle help link -->
                <div style="padding:14px 20px;border-top:1px solid #eef2f7;background:#fbfdff;font-size:13px;color:#6b7280;display:flex;justify-content:space-between;align-items:center;">
                    <div style="font-size:12px;color:#94a3b8">{__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</div>
                </div>
            </div>
        </div>
    </body>
</html>
"""

            # Attach both parts (plain and html)
            message.attach(MIMEText(plain_text, 'plain'))
            message.attach(MIMEText(html, 'html'))
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send message
            sent_message = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"✅ Sent email: {sent_message['id']}")
            
            return {
                "success": True,
                "message_id": sent_message['id'],
                "thread_id": sent_message.get('threadId'),
                "to": params.get('to'),
                "subject": params.get('subject')
            }
            
        except HttpError as e:
            logger.error(f"❌ HTTP error sending email: {e}")
            return {
                "success": False,
                "error": f"Gmail API error: {e.reason}"
            }
    
    async def _list_emails(self, service, params: Dict[str, Any]) -> Dict[str, Any]:
        """List recent emails from inbox, excluding spam and trash."""
        try:
            max_results = params.get('max_results', 10)
            query = params.get('query', None)
            page_token = params.get('page_token', None)
            
            # Build request parameters
            list_params = {
                'userId': 'me',
                'maxResults': max_results
            }
            
            # Add page token for pagination
            if page_token:
                list_params['pageToken'] = page_token
            
            # Default filter: primary inbox only (excludes promotions, social, updates, forums)
            # Also exclude spam and trash for safety
            if not query:
                query = 'category:primary -in:spam -in:trash'
            
            # Add query filter
            list_params['q'] = query
            
            results = service.users().messages().list(**list_params).execute()
            
            messages = results.get('messages', [])
            next_page_token = results.get('nextPageToken')
            
            # Get message details
            detailed_messages = []
            for msg in messages:
                msg_data = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()
                
                headers = {h['name']: h['value'] for h in msg_data.get('payload', {}).get('headers', [])}
                
                detailed_messages.append({
                    'id': msg['id'],
                    'thread_id': msg_data.get('threadId'),
                    'from': headers.get('From', ''),
                    'subject': headers.get('Subject', 'No Subject'),
                    'date': headers.get('Date', ''),
                    'snippet': msg_data.get('snippet', '')
                })
            
            logger.info(f"✅ Listed {len(detailed_messages)} emails")

            return {
                "success": True,
                "messages": detailed_messages,
                "count": len(detailed_messages),
                "next_page_token": next_page_token
            }
            
        except HttpError as e:
            logger.error(f"❌ HTTP error listing emails: {e}")
            return {
                "success": False,
                "error": f"Gmail API error: {e.reason}"
            }
    
    async def _read_email(self, service, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a specific email."""
        try:
            message_id = params.get('message_id')
            if not message_id:
                return {"success": False, "error": "message_id is required for read"}
            
            msg = service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}
            
            # Extract body
            body = ''
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        body_data = part['body'].get('data', '')
                        if body_data:
                            body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                            break
            else:
                body_data = msg['payload']['body'].get('data', '')
                if body_data:
                    body = base64.urlsafe_b64decode(body_data).decode('utf-8')
            
            logger.info(f"✅ Read email: {message_id}")
            
            return {
                "success": True,
                "id": message_id,
                "thread_id": msg.get('threadId'),
                "from": headers.get('From', ''),
                "to": headers.get('To', ''),
                "subject": headers.get('Subject', 'No Subject'),
                "date": headers.get('Date', ''),
                "body": body,
                "snippet": msg.get('snippet', '')
            }
            
        except HttpError as e:
            logger.error(f"❌ HTTP error reading email: {e}")
            return {
                "success": False,
                "error": f"Gmail API error: {e.reason}"
            }
    
    async def _search_emails(self, service, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search emails by query."""
        try:
            query = params.get('query', '')
            max_results = params.get('max_results', 10)
            
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            # Get message details
            detailed_messages = []
            for msg in messages:
                msg_data = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()
                
                headers = {h['name']: h['value'] for h in msg_data.get('payload', {}).get('headers', [])}
                
                detailed_messages.append({
                    'id': msg['id'],
                    'thread_id': msg_data.get('threadId'),
                    'from': headers.get('From', ''),
                    'subject': headers.get('Subject', 'No Subject'),
                    'date': headers.get('Date', ''),
                    'snippet': msg_data.get('snippet', '')
                })
            
            logger.info(f"✅ Found {len(detailed_messages)} emails matching query: {query}")
            
            return {
                "success": True,
                "query": query,
                "messages": detailed_messages,
                "count": len(detailed_messages)
            }
            
        except HttpError as e:
            logger.error(f"❌ HTTP error searching emails: {e}")
            return {
                "success": False,
                "error": f"Gmail API error: {e.reason}"
            }
    
    async def _delete_email(self, service, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete an email."""
        try:
            message_id = params.get('message_id')
            if not message_id:
                return {"success": False, "error": "message_id is required for delete"}
            
            service.users().messages().delete(userId='me', id=message_id).execute()
            
            logger.info(f"✅ Deleted email: {message_id}")
            
            return {
                "success": True,
                "message": f"Email {message_id} deleted successfully"
            }
            
        except HttpError as e:
            logger.error(f"❌ HTTP error deleting email: {e}")
            return {
                "success": False,
                "error": f"Gmail API error: {e.reason}"
            }


# Singleton instance
_email_tool: Optional[EmailTool] = None


def get_email_tool() -> EmailTool:
    """Get or create EmailTool singleton."""
    global _email_tool
    if _email_tool is None:
        _email_tool = EmailTool()
    return _email_tool
