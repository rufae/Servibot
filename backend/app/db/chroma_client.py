"""
Centralized ChromaDB client management
"""
import os
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

_client = None
_collection = None


def get_chroma_client():
    """Get or create a persistent ChromaDB client.
    
    Returns the singleton client instance.
    """
    global _client
    
    if _client is not None:
        return _client
    
    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings
    except ImportError as e:
        logger.error(f"chromadb not available: {e}")
        raise RuntimeError("chromadb not installed")
    
    persist_dir = os.path.abspath(settings.VECTOR_DB_PATH)
    os.makedirs(persist_dir, exist_ok=True)
    
    try:
        # Try recommended Settings import with telemetry disabled
        _client = chromadb.Client(
            ChromaSettings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=persist_dir,
                anonymized_telemetry=False  # Disable telemetry
            )
        )
        logger.info(f"✅ ChromaDB client initialized with persistence: {persist_dir}")
    except Exception as e:
        # Fallback to old config path if new one fails
        try:
            _client = chromadb.Client(
                chromadb.config.Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=persist_dir
                )
            )
            logger.info(f"✅ ChromaDB client initialized (fallback config)")
        except Exception:
            # Last resort: non-persistent client
            logger.warning("Failed to create persistent client, using in-memory")
            _client = chromadb.Client()
    
    return _client


def get_collection(collection_name: str = "servibot_docs"):
    """Get or create the default collection.
    
    Returns the collection object.
    """
    global _collection
    
    # Always get fresh collection in case of updates
    client = get_chroma_client()
    
    try:
        _collection = client.get_collection(collection_name)
        logger.debug(f"Retrieved existing collection: {collection_name}")
    except Exception:
        _collection = client.create_collection(name=collection_name)
        logger.info(f"Created new collection: {collection_name}")
    
    return _collection


def persist_client():
    """Persist ChromaDB data to disk if supported."""
    global _client
    
    if _client is None:
        return
    
    try:
        _client.persist()
        logger.debug("ChromaDB persisted to disk")
    except AttributeError:
        # persist() not available in newer versions (auto-persists)
        pass
    except Exception as e:
        logger.warning(f"Failed to persist ChromaDB: {e}")


def reset_client():
    """Reset the singleton client (useful for testing)."""
    global _client, _collection
    _client = None
    _collection = None
