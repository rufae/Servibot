"""
Health Check Endpoint
Provides system health and status information.
"""
from fastapi import APIRouter
from datetime import datetime
import psutil
import os

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint that returns system status.
    
    Returns:
        dict: System health information
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint for deployment orchestration.
    
    Returns:
        dict: Readiness status
    """
    # TODO: Add checks for vector DB, external APIs, etc.
    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat()
    }
