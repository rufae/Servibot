"""
Google Contacts Tool - Access user contacts via Google People API
"""
import logging
from typing import Dict, Any, List, Optional
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)


class ContactsTool:
    """Tool for accessing Google Contacts via People API"""
    
    def __init__(self):
        self.name = "contacts"
        self.description = "Access and search user's Google contacts"
    
    async def execute(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Execute contacts operations.
        
        Actions:
        - list: Get all contacts
        - search: Search contacts by name
        - get: Get specific contact details
        """
        action = params.get("action", "list")
        
        try:
            # Get user's Google credentials
            from app.db.sqlite_client import get_sqlite_client
            db = get_sqlite_client()
            user = db.get_user_by_id(int(user_id))
            
            if not user:
                return {"success": False, "error": "User not found"}
            
            google_token = user.get('google_access_token')
            google_refresh = user.get('google_refresh_token')

            # If tokens are not present on the users table, try the oauth_tokens table
            if not google_token:
                try:
                    from app.core.config import settings
                    import sqlite3
                    db_path = settings.SQLITE_DB_PATH
                    conn = sqlite3.connect(db_path)
                    cur = conn.cursor()
                    # Try to find a google oauth token row for this user (fallback to any google token)
                    cur.execute(
                        "SELECT access_token, refresh_token, scope FROM oauth_tokens WHERE provider = 'google' ORDER BY id DESC LIMIT 1"
                    )
                    row = cur.fetchone()
                    conn.close()
                    if row:
                        google_token, google_refresh, _ = row
                except Exception:
                    # ignore and fallback to requires_auth below
                    pass

            if not google_token:
                return {
                    "success": False,
                    "error": "Google account not connected. Please connect your Google account first.",
                    "requires_auth": True
                }
            
            # Build credentials
            from app.core.config import settings
            credentials = Credentials(
                token=google_token,
                refresh_token=google_refresh,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_OAUTH_CLIENT_ID,
                client_secret=settings.GOOGLE_OAUTH_CLIENT_SECRET
            )
            
            # Build People API service
            service = build('people', 'v1', credentials=credentials)
            
            if action == "list":
                return await self._list_contacts(service, params)
            elif action == "search":
                return await self._search_contacts(service, params)
            elif action == "get":
                return await self._get_contact(service, params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"❌ Contacts tool error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _list_contacts(self, service, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all contacts."""
        import time
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # Support pagination to retrieve more than a single page (e.g. >200 contacts)
                page_size = int(params.get("page_size", 200))
                page_token = params.get("page_token")

                all_connections = []
                request_params = {
                    'resourceName': 'people/me',
                    'pageSize': page_size,
                    'personFields': 'names,emailAddresses,phoneNumbers,photos'
                }

                if page_token:
                    request_params['pageToken'] = page_token

                while True:
                    results = service.people().connections().list(**request_params).execute()
                    connections = results.get('connections', [])
                    if connections:
                        all_connections.extend(connections)

                    next_token = results.get('nextPageToken')
                    if not next_token:
                        break
                    # prepare next request
                    request_params['pageToken'] = next_token

                contacts = self._format_contacts(all_connections)

                logger.info(f"📇 Listed {len(contacts)} contacts (paginated)")

                return {
                    "success": True,
                    "contacts": contacts,
                    "total": len(contacts),
                    "next_page_token": None
                }
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {retry_delay}s: {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    logger.error(f"❌ Error listing contacts after {max_retries} attempts: {e}")
                    return {"success": False, "error": f"Failed to list contacts: {str(e)}"}
    
    async def _search_contacts(self, service, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search contacts by name."""
        try:
            import unicodedata
            
            query = params.get("query", "")
            if not query:
                return {"success": False, "error": "Search query is required"}
            
            # Normalize unicode (handle emojis, accents, etc.)
            query_normalized = unicodedata.normalize('NFKC', query).lower().strip()
            query_lower = query.lower().strip()
            # Prefer using people.searchContacts which searches across all saved and other contacts
            try:
                resp = service.people().searchContacts(
                    query=query,
                    pageSize=1000,
                    readMask='names,emailAddresses,phoneNumbers,photos'
                ).execute()

                results = resp.get('results', [])
                formatted = []
                for item in results:
                    person = item.get('person')
                    if person:
                        formatted.append(self._format_single_contact(person))

                logger.info(f"🔍 searchContacts found {len(formatted)} matches for '{query}'")
                return {"success": True, "contacts": formatted, "total": len(formatted), "query": query}
            except Exception:
                # Fallback: paginate through connections and filter locally
                all_connections = []
                request_params = {
                    'resourceName': 'people/me',
                    'pageSize': 1000,
                    'personFields': 'names,emailAddresses,phoneNumbers,photos'
                }
                while True:
                    results = service.people().connections().list(**request_params).execute()
                    connections = results.get('connections', [])
                    if connections:
                        all_connections.extend(connections)
                    next_token = results.get('nextPageToken')
                    if not next_token:
                        break
                    request_params['pageToken'] = next_token

                all_contacts = self._format_contacts(all_connections)
                # Match both original and normalized versions
                matching_contacts = []
                for c in all_contacts:
                    name = c.get('name', '')
                    name_lower = name.lower()
                    name_normalized = unicodedata.normalize('NFKC', name).lower()
                    if query_lower in name_lower or query_normalized in name_normalized:
                        matching_contacts.append(c)
                
                logger.info(f"🔍 Fallback found {len(matching_contacts)} contacts matching '{query}'")
                return {"success": True, "contacts": matching_contacts, "total": len(matching_contacts), "query": query}
            
        except Exception as e:
            logger.error(f"Error searching contacts: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_contact(self, service, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get specific contact by resource name."""
        try:
            resource_name = params.get("resource_name")
            
            if not resource_name:
                return {"success": False, "error": "resource_name is required"}
            
            person = service.people().get(
                resourceName=resource_name,
                personFields='names,emailAddresses,phoneNumbers,photos,addresses,organizations'
            ).execute()
            
            contact = self._format_single_contact(person)
            
            return {
                "success": True,
                "contact": contact
            }
            
        except Exception as e:
            logger.error(f"Error getting contact: {e}")
            return {"success": False, "error": str(e)}
    
    def _format_contacts(self, connections: List[Dict]) -> List[Dict]:
        """Format contacts from People API response."""
        formatted = []
        
        for person in connections:
            formatted.append(self._format_single_contact(person))
        
        return formatted
    
    def _format_single_contact(self, person: Dict) -> Dict:
        """Format a single contact."""
        # Get name
        names = person.get('names', [])
        display_name = names[0].get('displayName', 'No Name') if names else 'No Name'
        
        # Get emails
        email_addresses = person.get('emailAddresses', [])
        emails = [e.get('value') for e in email_addresses if e.get('value')]
        primary_email = emails[0] if emails else None
        
        # Get phone numbers
        phone_numbers = person.get('phoneNumbers', [])
        phones = [p.get('value') for p in phone_numbers if p.get('value')]
        primary_phone = phones[0] if phones else None
        
        # Get photo
        photos = person.get('photos', [])
        photo_url = photos[0].get('url') if photos else None
        
        return {
            'resource_name': person.get('resourceName'),
            'name': display_name,
            'email': primary_email,
            'emails': emails,
            'phone': primary_phone,
            'phones': phones,
            'photo_url': photo_url
        }


def get_contacts_tool() -> ContactsTool:
    """Get a singleton instance of the contacts tool."""
    return ContactsTool()
