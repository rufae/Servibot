"""
Tests for Google OAuth integration
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.services.google_oauth import (
    build_oauth_flow,
    get_authorization_url,
    credentials_to_dict,
    credentials_from_dict
)
from app.tools.calendar_tool import CalendarTool
from app.tools.email_tool import EmailTool


class TestGoogleOAuth:
    """Test Google OAuth service."""
    
    def test_build_oauth_flow(self):
        """Test building OAuth flow."""
        flow = build_oauth_flow()
        assert flow is not None
        assert flow.redirect_uri == "http://localhost:8000/auth/google/callback"
    
    def test_get_authorization_url(self):
        """Test getting authorization URL."""
        flow = build_oauth_flow()
        auth_url, state = get_authorization_url(flow)
        
        assert auth_url is not None
        assert "accounts.google.com" in auth_url
        assert "oauth2" in auth_url
        assert state is not None
    
    def test_credentials_to_dict(self):
        """Test converting credentials to dict."""
        mock_creds = Mock()
        mock_creds.token = "test_token"
        mock_creds.refresh_token = "test_refresh"
        mock_creds.token_uri = "https://oauth2.googleapis.com/token"
        mock_creds.client_id = "test_client_id"
        mock_creds.client_secret = "test_client_secret"
        mock_creds.scopes = ["calendar", "gmail"]
        mock_creds.expiry = datetime(2026, 1, 15, 10, 0, 0)
        
        result = credentials_to_dict(mock_creds)
        
        assert result['token'] == "test_token"
        assert result['refresh_token'] == "test_refresh"
        assert result['scopes'] == "calendar,gmail"
        assert result['expiry'] is not None
    
    def test_credentials_from_dict(self):
        """Test creating credentials from dict."""
        creds_dict = {
            'token': "test_token",
            'refresh_token': "test_refresh",
            'token_uri': "https://oauth2.googleapis.com/token",
            'client_id': "test_client_id",
            'client_secret': "test_client_secret",
            'scopes': "calendar,gmail",
            'expiry': int(datetime(2026, 1, 15, 10, 0, 0).timestamp())
        }
        
        creds = credentials_from_dict(creds_dict)
        
        assert creds.token == "test_token"
        assert creds.refresh_token == "test_refresh"
        assert creds.client_id == "test_client_id"


class TestCalendarTool:
    """Test CalendarTool."""
    
    def test_tool_properties(self):
        """Test tool basic properties."""
        tool = CalendarTool()
        assert tool.name == "calendar"
        assert tool.description is not None
        assert len(tool.description) > 0
    
    def test_get_schema(self):
        """Test getting tool schema."""
        tool = CalendarTool()
        schema = tool.get_schema()
        
        assert schema.name == "calendar"
        assert len(schema.parameters) > 0
        
        # Check that action parameter exists
        action_param = next((p for p in schema.parameters if p.name == "action"), None)
        assert action_param is not None
        assert action_param.required is True
    
    @pytest.mark.asyncio
    async def test_execute_without_credentials(self):
        """Test executing without credentials returns error."""
        tool = CalendarTool()
        
        with patch('app.tools.calendar_tool.get_credentials_for_user', return_value=None):
            result = await tool.execute({
                "action": "list"
            }, user_id="test_user")
            
            assert result['success'] is False
            assert "not authenticated" in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_create_event_with_mock(self):
        """Test creating event with mocked credentials."""
        tool = CalendarTool()
        
        mock_creds = Mock()
        mock_service = MagicMock()
        mock_event = {
            'id': 'test_event_123',
            'htmlLink': 'https://calendar.google.com/event?eid=test',
            'summary': 'Test Event',
            'start': {'dateTime': '2026-01-15T10:00:00Z'},
            'end': {'dateTime': '2026-01-15T11:00:00Z'}
        }
        
        mock_service.events().insert().execute.return_value = mock_event
        
        with patch('app.tools.calendar_tool.get_credentials_for_user', return_value=mock_creds):
            with patch('app.tools.calendar_tool.build', return_value=mock_service):
                result = await tool.execute({
                    "action": "create",
                    "summary": "Test Event",
                    "start_time": "2026-01-15T10:00:00Z",
                    "end_time": "2026-01-15T11:00:00Z"
                }, user_id="test_user")
                
                assert result['success'] is True
                assert result['event_id'] == 'test_event_123'


class TestEmailTool:
    """Test EmailTool."""
    
    def test_tool_properties(self):
        """Test tool basic properties."""
        tool = EmailTool()
        assert tool.name == "email"
        assert tool.description is not None
        assert len(tool.description) > 0
    
    def test_get_schema(self):
        """Test getting tool schema."""
        tool = EmailTool()
        schema = tool.get_schema()
        
        assert schema.name == "email"
        assert len(schema.parameters) > 0
        
        # Check that action parameter exists
        action_param = next((p for p in schema.parameters if p.name == "action"), None)
        assert action_param is not None
        assert action_param.required is True
    
    @pytest.mark.asyncio
    async def test_execute_without_credentials(self):
        """Test executing without credentials returns error."""
        tool = EmailTool()
        
        with patch('app.tools.email_tool.get_credentials_for_user', return_value=None):
            result = await tool.execute({
                "action": "list"
            }, user_id="test_user")
            
            assert result['success'] is False
            assert "not authenticated" in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_send_email_with_mock(self):
        """Test sending email with mocked credentials."""
        tool = EmailTool()
        
        mock_creds = Mock()
        mock_service = MagicMock()
        mock_sent = {
            'id': 'msg_123',
            'threadId': 'thread_456'
        }
        
        mock_service.users().messages().send().execute.return_value = mock_sent
        
        with patch('app.tools.email_tool.get_credentials_for_user', return_value=mock_creds):
            with patch('app.tools.email_tool.build', return_value=mock_service):
                result = await tool.execute({
                    "action": "send",
                    "to": "test@example.com",
                    "subject": "Test Email",
                    "body": "This is a test"
                }, user_id="test_user")
                
                assert result['success'] is True
                assert result['message_id'] == 'msg_123'
