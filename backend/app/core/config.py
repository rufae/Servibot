"""
Application Configuration Settings
Manages environment variables and application settings.
"""
from typing import List, Any, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import os
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "ServiBot"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)

    # API Keys
    OPENAI_API_KEY: str = Field(default="")
    ELEVENLABS_API_KEY: str = Field(default="")
    HUGGINGFACE_API_KEY: str = Field(default="")

    # Google APIs
    GOOGLE_CALENDAR_CREDENTIALS: str = Field(default="")
    GMAIL_CREDENTIALS: str = Field(default="")

    # Third-party integrations
    NOTION_API_KEY: str = Field(default="")
    TODOIST_API_KEY: str = Field(default="")

    # Database
    VECTOR_DB_PATH: str = Field(default="./data/vector_db")
    SQLITE_DB_PATH: str = Field(default="./data/servibot.db")

    # Upload settings
    UPLOAD_DIR: str = Field(default="./data/uploads")
    MAX_UPLOAD_SIZE: int = Field(default=10_485_760)  # 10MB
    # Upload status persistence
    UPLOAD_STATUS_FILE: str = Field(default="./data/upload_status.json")
    # Indexing retry policy
    INDEX_RETRY_MAX: int = Field(default=3)
    INDEX_RETRY_INTERVAL_SECONDS: int = Field(default=30)

    # CORS - accept either JSON array or comma-separated string in env
    # Use type Any to avoid pydantic_settings attempting JSON decode on startup
    CORS_ORIGINS: Any = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]
    )

    # RAG Settings
    CHUNK_SIZE: int = Field(default=1000)
    CHUNK_OVERLAP: int = Field(default=200)
    TOP_K_RESULTS: int = Field(default=5)

    # Agent Settings
    MAX_ITERATIONS: int = Field(default=10)
    AGENT_TIMEOUT: int = Field(default=300)  # seconds
    # Mocks
    USE_MOCKS: bool = Field(default=True)
    MOCK_OUTPUT_DIR: str = Field(default="./data/mock_outputs")

    # Language Model settings
    LM_API_URL: Optional[str] = Field(None, env="LM_API_URL")
    LM_API_KEY: Optional[str] = Field(None, env="LM_API_KEY")
    LM_USE_LOCAL_LM: bool = Field(False, env="LM_USE_LOCAL_LM")
    LM_MODEL: Optional[str] = Field(None, env="LM_MODEL")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

    # Validator to accept comma-separated env var values
    @field_validator("CORS_ORIGINS", mode="before")
    def _parse_cors_origins(cls, v: Any) -> List[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            # If JSON-like, parse
            if s.startswith("["):
                try:
                    return json.loads(s)
                except Exception:
                    pass
            # Comma separated
            return [p.strip() for p in s.split(",") if p.strip()]
        return [str(v)]


# Global settings instance
settings = Settings()
