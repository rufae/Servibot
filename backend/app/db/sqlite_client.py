"""
SQLite Database Client for ServiBot
Manages OAuth tokens and other persistent data.
"""
import sqlite3
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class SQLiteClient:
    """SQLite database client for managing OAuth tokens and app data."""
    
    def __init__(self, db_path: str = None):
        """Initialize SQLite client."""
        self.db_path = db_path or settings.SQLITE_DB_PATH
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create oauth_tokens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS oauth_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                user_id TEXT,
                sub TEXT,
                access_token TEXT,
                refresh_token TEXT,
                scope TEXT,
                token_uri TEXT,
                client_id TEXT,
                client_secret TEXT,
                expires_at INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on provider and sub for fast lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_oauth_provider_sub 
            ON oauth_tokens(provider, sub)
        """)
        
        # Create index on user_id for fast lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_oauth_user_id 
            ON oauth_tokens(user_id)
        """)
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                google_id TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                picture TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on google_id for fast lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_google_id 
            ON users(google_id)
        """)
        
        # Create index on email for fast lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email 
            ON users(email)
        """)
        
        conn.commit()
        conn.close()
        logger.info("✅ SQLite database initialized")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a new database connection."""
        return sqlite3.connect(self.db_path)
    
    def save_oauth_token(
        self,
        provider: str,
        credentials_dict: Dict[str, Any],
        user_id: Optional[str] = None,
        sub: Optional[str] = None
    ) -> int:
        """
        Save or update OAuth token.
        
        Args:
            provider: OAuth provider (e.g., 'google')
            credentials_dict: Dictionary with token data
            user_id: Optional local user identifier
            sub: OAuth subject (Google user ID)
        
        Returns:
            The ID of the saved token record
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if token already exists
        cursor.execute("""
            SELECT id FROM oauth_tokens 
            WHERE provider = ? AND (sub = ? OR user_id = ?)
        """, (provider, sub, user_id))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing token
            cursor.execute("""
                UPDATE oauth_tokens 
                SET access_token = ?,
                    refresh_token = ?,
                    scope = ?,
                    token_uri = ?,
                    client_id = ?,
                    client_secret = ?,
                    expires_at = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                credentials_dict.get('token'),
                credentials_dict.get('refresh_token'),
                credentials_dict.get('scopes'),
                credentials_dict.get('token_uri'),
                credentials_dict.get('client_id'),
                credentials_dict.get('client_secret'),
                credentials_dict.get('expiry'),
                datetime.utcnow().isoformat(),
                existing[0]
            ))
            token_id = existing[0]
            logger.info(f"✅ Updated OAuth token for {provider} (id={token_id})")
        else:
            # Insert new token
            cursor.execute("""
                INSERT INTO oauth_tokens (
                    provider, user_id, sub, access_token, refresh_token,
                    scope, token_uri, client_id, client_secret, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                provider,
                user_id,
                sub,
                credentials_dict.get('token'),
                credentials_dict.get('refresh_token'),
                credentials_dict.get('scopes'),
                credentials_dict.get('token_uri'),
                credentials_dict.get('client_id'),
                credentials_dict.get('client_secret'),
                credentials_dict.get('expiry')
            ))
            token_id = cursor.lastrowid
            logger.info(f"✅ Saved new OAuth token for {provider} (id={token_id})")
        
        conn.commit()
        conn.close()
        
        return token_id
    
    def get_oauth_token(
        self,
        provider: str,
        user_id: Optional[str] = None,
        sub: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve OAuth token.
        
        Args:
            provider: OAuth provider (e.g., 'google')
            user_id: Optional local user identifier
            sub: OAuth subject (Google user ID)
        
        Returns:
            Dictionary with token data or None if not found
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, provider, user_id, sub, access_token, refresh_token,
                   scope, token_uri, client_id, client_secret, expires_at,
                   created_at, updated_at
            FROM oauth_tokens
            WHERE provider = ? AND (sub = ? OR user_id = ?)
            ORDER BY updated_at DESC
            LIMIT 1
        """, (provider, sub, user_id))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            'id': row[0],
            'provider': row[1],
            'user_id': row[2],
            'sub': row[3],
            'token': row[4],
            'refresh_token': row[5],
            'scopes': row[6],
            'token_uri': row[7],
            'client_id': row[8],
            'client_secret': row[9],
            'expiry': row[10],
            'created_at': row[11],
            'updated_at': row[12]
        }
    
    def delete_oauth_token(
        self,
        provider: str,
        user_id: Optional[str] = None,
        sub: Optional[str] = None
    ) -> bool:
        """
        Delete OAuth token.
        
        Args:
            provider: OAuth provider (e.g., 'google')
            user_id: Optional local user identifier
            sub: OAuth subject (Google user ID)
        
        Returns:
            True if deleted, False if not found
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM oauth_tokens
            WHERE provider = ? AND (sub = ? OR user_id = ?)
        """, (provider, sub, user_id))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if deleted:
            logger.info(f"✅ Deleted OAuth token for {provider}")
        
        return deleted
    
    def create_or_update_user(
        self,
        google_id: str,
        email: str,
        name: Optional[str] = None,
        picture: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create or update user in database.
        
        Args:
            google_id: Google user ID
            email: User email
            name: User name
            picture: Profile picture URL
            
        Returns:
            User data dict
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id, google_id, email, name, picture, created_at FROM users WHERE google_id = ?", (google_id,))
        row = cursor.fetchone()
        
        if row:
            # Update existing user
            cursor.execute("""
                UPDATE users 
                SET email = ?, name = ?, picture = ?, last_login = CURRENT_TIMESTAMP
                WHERE google_id = ?
            """, (email, name, picture, google_id))
            user_id = row[0]
            logger.info(f"✅ Updated user: {email}")
        else:
            # Create new user
            cursor.execute("""
                INSERT INTO users (google_id, email, name, picture)
                VALUES (?, ?, ?, ?)
            """, (google_id, email, name, picture))
            user_id = cursor.lastrowid
            logger.info(f"✅ Created new user: {email}")
        
        conn.commit()
        conn.close()
        
        return {
            'id': user_id,
            'google_id': google_id,
            'email': email,
            'name': name,
            'picture': picture
        }
    
    def get_user_by_google_id(self, google_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Google ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, google_id, email, name, picture, created_at, last_login
            FROM users WHERE google_id = ?
        """, (google_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            'id': row[0],
            'google_id': row[1],
            'email': row[2],
            'name': row[3],
            'picture': row[4],
            'created_at': row[5],
            'last_login': row[6]
        }
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, google_id, email, name, picture, created_at, last_login
            FROM users WHERE id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            'id': row[0],
            'google_id': row[1],
            'email': row[2],
            'name': row[3],
            'picture': row[4],
            'created_at': row[5],
            'last_login': row[6]
        }


# Singleton instance
_sqlite_client: Optional[SQLiteClient] = None


def get_sqlite_client() -> SQLiteClient:
    """Get or create SQLite client singleton."""
    global _sqlite_client
    if _sqlite_client is None:
        _sqlite_client = SQLiteClient()
    return _sqlite_client
