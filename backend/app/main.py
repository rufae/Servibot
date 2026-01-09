"""
ServiBot Backend - FastAPI Main Application
Main entry point for the ServiBot autonomous agent backend.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.api import chat, upload, health, rag, voice, generate
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting ServiBot Backend...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Auto-index all uploaded files on startup
    try:
        import os
        import threading
        from app.rag.ingest import index_file
        
        uploads_dir = settings.UPLOAD_DIR
        if os.path.exists(uploads_dir):
            files = [f for f in os.listdir(uploads_dir) if os.path.isfile(os.path.join(uploads_dir, f))]
            
            if files:
                logger.info(f"📁 Found {len(files)} files to auto-index")
                
                def auto_index_files():
                    """Background thread to index all files"""
                    indexed_count = 0
                    error_count = 0
                    
                    for filename in files:
                        try:
                            file_path = os.path.join(uploads_dir, filename)
                            logger.info(f"🔄 Auto-indexing: {filename}")
                            result = index_file(file_path, file_id=filename)
                            
                            if result.get("status") == "success":
                                indexed_count += 1
                                logger.info(f"✅ Indexed: {filename} ({result.get('indexed', 0)} chunks)")
                            else:
                                error_count += 1
                                logger.warning(f"⚠️ Failed to index {filename}: {result.get('message')}")
                        except Exception as e:
                            error_count += 1
                            logger.error(f"❌ Error auto-indexing {filename}: {e}")
                    
                    logger.info(f"✅ Auto-indexing complete: {indexed_count} success, {error_count} errors")
                
                # Start in background thread to not block startup
                threading.Thread(target=auto_index_files, daemon=True).start()
            else:
                logger.info("📂 No files found in uploads directory")
        else:
            logger.info(f"📂 Uploads directory not found: {uploads_dir}")
    except Exception as e:
        logger.error(f"❌ Error during auto-indexing: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down ServiBot Backend...")


# Initialize FastAPI app
app = FastAPI(
    title="ServiBot API",
    description="Autonomous multimodal agent for personal task management with RAG, voice, and automation",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(rag.router, prefix="/api", tags=["RAG"])
app.include_router(voice.router, prefix="/api", tags=["Voice"])
app.include_router(generate.router, prefix="/api", tags=["Generate"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "ServiBot API",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/api/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
