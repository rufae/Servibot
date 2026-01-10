"""
Upload API Endpoint
Handles file uploads (PDFs, images) for RAG ingestion.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import mimetypes
from typing import List
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
import json
import threading
import time

from app.core.config import settings
from app.rag.ingest import index_file, delete_file_from_chroma, clear_all_chroma

# Upload status persistence and in-memory store
UPLOAD_STATUS_FILE = os.path.abspath(settings.UPLOAD_STATUS_FILE)
UPLOAD_STATUS_LOCK = threading.Lock()

def _load_upload_status() -> dict:
    try:
        if os.path.exists(UPLOAD_STATUS_FILE):
            with open(UPLOAD_STATUS_FILE, "r", encoding="utf-8") as fh:
                return json.load(fh)
    except Exception:
        logger = logging.getLogger(__name__)
        logger.exception("Failed to load upload status file; starting with empty status store")
    return {}

def _save_upload_status():
    try:
        d = os.path.dirname(UPLOAD_STATUS_FILE)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
        with open(UPLOAD_STATUS_FILE, "w", encoding="utf-8") as fh:
            json.dump(UPLOAD_STATUS, fh, ensure_ascii=False, indent=2)
    except Exception:
        logger = logging.getLogger(__name__)
        logger.exception("Failed to save upload status to disk")

# Simple in-memory status store for uploads: file_id -> {status, message, attempts}
UPLOAD_STATUS: dict = _load_upload_status()

logger = logging.getLogger(__name__)
router = APIRouter()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


# Background retry worker: reattempt indexing for failed files
def _retry_worker():
    log = logging.getLogger(__name__)
    while True:
        try:
            with UPLOAD_STATUS_LOCK:
                items = list(UPLOAD_STATUS.items())
            for fid, st in items:
                try:
                    if not isinstance(st, dict):
                        continue
                    status = st.get("status")
                    attempts = st.get("attempts", 0)
                    
                    # Only retry if it's an actual error (not empty file or extraction issues)
                    if status == "error" and attempts < settings.INDEX_RETRY_MAX:
                        # Check if this is a permanent error (file empty, corrupted, etc.)
                        error_msg = st.get("message", "").lower()
                        permanent_errors = [
                            "file is empty",
                            "no text could be extracted",
                            "password-protected",
                            "unsupported format",
                            "file not found"
                        ]
                        
                        is_permanent = any(perm in error_msg for perm in permanent_errors)
                        
                        if is_permanent:
                            log.info(f"Skipping retry for {fid}: permanent error ({error_msg[:100]})")
                            continue
                        
                        log.info(f"Retrying indexing for {fid} (attempt {attempts+1}/{settings.INDEX_RETRY_MAX})")
                        # increment attempts
                        with UPLOAD_STATUS_LOCK:
                            UPLOAD_STATUS.setdefault(fid, {})
                            UPLOAD_STATUS[fid]["status"] = "retrying"
                            UPLOAD_STATUS[fid]["attempts"] = attempts + 1
                            UPLOAD_STATUS[fid]["message"] = f"Retrying... (attempt {attempts+1})"
                            _save_upload_status()

                        # attempt to index
                        file_path = os.path.join(settings.UPLOAD_DIR, fid)
                        try:
                            res = index_file(file_path, file_id=fid)
                            with UPLOAD_STATUS_LOCK:
                                UPLOAD_STATUS[fid]["debug"] = res
                                if res.get("status") == "success":
                                    UPLOAD_STATUS[fid]["status"] = "indexed"
                                    UPLOAD_STATUS[fid]["message"] = f"✓ Indexed {res.get('indexed', 0)} chunks (after retry)"
                                    log.info(f"Retry successful for {fid}")
                                else:
                                    UPLOAD_STATUS[fid]["status"] = "error"
                                    UPLOAD_STATUS[fid]["message"] = f"✗ {res.get('message', 'Retry failed')}"
                                    log.warning(f"Retry failed for {fid}: {res.get('message')}")
                                _save_upload_status()
                        except Exception as e:
                            with UPLOAD_STATUS_LOCK:
                                UPLOAD_STATUS[fid]["status"] = "error"
                                UPLOAD_STATUS[fid]["message"] = f"✗ Retry exception: {str(e)[:150]}"
                                _save_upload_status()
                except Exception:
                    log.exception(f"Error while processing retry for {fid}")
        except Exception:
            logger.exception("Retry worker encountered an error")
        time.sleep(settings.INDEX_RETRY_INTERVAL_SECONDS)


# Start retry worker thread
try:
    t = threading.Thread(target=_retry_worker, daemon=True)
    t.start()
except Exception:
    logger.exception("Failed to start upload retry worker thread")


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file (PDF or image) for processing and RAG ingestion.
    
    Args:
        file: Uploaded file
        
    Returns:
        dict: Upload status and file information
    """
    try:
        # Logging de debugging para multipart/form-data
        logger.info(f"Received upload request: filename={file.filename}, content_type={file.content_type}")
        
        # Validar que filename no sea None o vacío
        if not file.filename:
            logger.error("Upload rejected: no filename provided")
            raise HTTPException(status_code=400, detail="No file provided or filename is empty")
        
        # Validate file size
        file_size = 0
        file_content = await file.read()
        file_size = len(file_content)
        
        logger.info(f"File size: {file_size} bytes")
        
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE / 1_048_576}MB"
            )
        
        # Validate file type
        allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.txt', '.md'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not supported. Allowed: {allowed_extensions}"
            )
        
        # Preserve original filename (avoid path components) and avoid collisions
        original_name = Path(file.filename).name
        safe_filename = original_name
        upload_dir = settings.UPLOAD_DIR
        candidate = safe_filename
        counter = 1
        # If a file with the same name already exists, append a numeric suffix
        while os.path.exists(os.path.join(upload_dir, candidate)):
            candidate = f"{Path(original_name).stem}_{counter}{Path(original_name).suffix}"
            counter += 1
        safe_filename = candidate
        file_path = os.path.join(upload_dir, safe_filename)
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"File uploaded successfully: {safe_filename}")

        # Initialize upload status
        with UPLOAD_STATUS_LOCK:
            UPLOAD_STATUS[safe_filename] = {"status": "uploaded", "message": "File uploaded, pending indexing", "attempts": 0}
            _save_upload_status()

        # Schedule background indexing via a thread: index will update UPLOAD_STATUS
        def _background_index(path: str, fid: str):
            log = logging.getLogger(__name__)
            try:
                with UPLOAD_STATUS_LOCK:
                    UPLOAD_STATUS.setdefault(fid, {})
                    UPLOAD_STATUS[fid]["status"] = "indexing"
                    UPLOAD_STATUS[fid]["message"] = "Indexing in progress"
                    UPLOAD_STATUS[fid].setdefault("attempts", 0)
                    _save_upload_status()

                log.info(f"Starting indexing for {fid} at {path}")
                
                # Call index_file with timeout protection
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError("Indexing took too long")
                
                # Set timeout for indexing (60 seconds)
                # Note: signal.alarm only works on Unix; on Windows, we rely on thread timeout
                res = None
                try:
                    res = index_file(path, file_id=fid)
                except Exception as idx_err:
                    log.exception(f"index_file raised exception for {fid}: {idx_err}")
                    res = {"status": "error", "message": f"Indexing exception: {str(idx_err)[:200]}"}
                
                # Always store result
                with UPLOAD_STATUS_LOCK:
                    UPLOAD_STATUS[fid].setdefault("debug", {})
                    UPLOAD_STATUS[fid]["debug"] = res
                    
                    if res and res.get("status") == "success":
                        UPLOAD_STATUS[fid]["status"] = "indexed"
                        UPLOAD_STATUS[fid]["message"] = f"✓ Indexed {res.get('indexed', 0)} chunks"
                        log.info(f"Successfully indexed {fid}: {res.get('indexed', 0)} chunks")
                    else:
                        UPLOAD_STATUS[fid]["status"] = "error"
                        error_msg = res.get("message", "Unknown indexing error") if res else "Indexing failed with no response"
                        UPLOAD_STATUS[fid]["message"] = f"✗ {error_msg}"
                        log.error(f"Indexing failed for {fid}: {error_msg}")
                    
                    _save_upload_status()
                    
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                log.exception(f"Background indexing critical failure for {fid}: {e}")
                with UPLOAD_STATUS_LOCK:
                    UPLOAD_STATUS[fid]["status"] = "error"
                    UPLOAD_STATUS[fid]["message"] = f"✗ Critical error: {str(e)[:150]}"
                    UPLOAD_STATUS[fid]["debug"] = {"exception": str(e), "traceback": tb}
                    UPLOAD_STATUS[fid]["attempts"] = UPLOAD_STATUS.get(fid, {}).get("attempts", 0) + 1
                    _save_upload_status()

        try:
            import threading
            threading.Thread(target=_background_index, args=(file_path, safe_filename), daemon=True).start()
        except Exception:
            _background_index(file_path, safe_filename)

        return {
            "status": "success",
            "filename": safe_filename,
            "size_bytes": file_size,
            "file_type": file_ext,
            "message": "File uploaded successfully. RAG ingestion pipeline started.",
            "file_id": safe_filename  # Use for tracking
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@router.get("/upload/status/{file_id}")
async def get_upload_status(file_id: str):
    """
    Get the processing status of an uploaded file.
    
    Args:
        file_id: File identifier
        
    Returns:
        dict: Processing status with debug info
    """
    # Return status from in-memory store if available
    st = UPLOAD_STATUS.get(file_id)
    if not st:
        raise HTTPException(status_code=404, detail="File status not found")
    
    return {
        "file_id": file_id, 
        "status": st.get("status"), 
        "message": st.get("message"), 
        "attempts": st.get("attempts", 0),
        "debug": st.get("debug", {})  # Include debug info for troubleshooting
    }


@router.get("/upload/list")
async def list_uploaded_files(skip: int = 0, limit: int = 50):
    """
    List all uploaded files with pagination support.
    
    Args:
        skip: Number of files to skip (for pagination)
        limit: Maximum number of files to return (default 50)
    
    Returns:
        dict: Paginated list of uploaded files with metadata
    """
    try:
        files = []
        for filename in os.listdir(settings.UPLOAD_DIR):
            file_path = os.path.join(settings.UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                files.append({
                    "filename": filename,
                    "size_bytes": stat.st_size,
                    "uploaded_at": datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
        
        # Sort by upload time (newest first)
        files_sorted = sorted(files, key=lambda x: x["uploaded_at"], reverse=True)
        
        # Apply pagination
        paginated_files = files_sorted[skip:skip + limit]
        
        return {
            "count": len(files_sorted),
            "skip": skip,
            "limit": limit,
            "has_more": len(files_sorted) > skip + limit,
            "files": paginated_files
        }
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")


@router.get("/upload/file/{file_id}")
async def get_uploaded_file(file_id: str):
    """
    Serve an uploaded file for download/viewing.

    Returns a FileResponse streaming the file as an attachment.
    """
    file_path = os.path.join(settings.UPLOAD_DIR, file_id)
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")

    # Use FileResponse to serve the file; let browser decide how to open it
    try:
        mime_type, _ = mimetypes.guess_type(file_path)
        media_type = mime_type or "application/octet-stream"
        
        # Add Content-Disposition header to force download
        headers = {"Content-Disposition": f'attachment; filename="{file_id}"'}
        
        return FileResponse(path=file_path, media_type=media_type, headers=headers, filename=file_id)
    except Exception as e:
        logger.exception(f"Failed to serve file {file_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to serve file: {str(e)}")


@router.post("/upload/cleanup-duplicates")
async def cleanup_duplicate_files():
    """
    Remove duplicate uploaded files, keeping only the most recent version of each.
    Files are considered duplicates if they have the same base name (ignoring timestamp prefix).
    
    Returns:
        Summary of removed files
    """
    try:
        files = []
        for filename in os.listdir(settings.UPLOAD_DIR):
            file_path = os.path.join(settings.UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                files.append({
                    "filename": filename,
                    "path": file_path,
                    "timestamp": stat.st_ctime
                })
        
        # Group by base name (removing timestamp prefix YYYYMMDD_HHMMSS_)
        from collections import defaultdict
        groups = defaultdict(list)
        for f in files:
            # Extract base name after timestamp prefix
            parts = f["filename"].split("_", 2)
            if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
                base_name = parts[2]
            else:
                base_name = f["filename"]
            groups[base_name].append(f)
        
        # For each group, keep only the most recent file
        removed = []
        kept = []
        for base_name, file_list in groups.items():
            if len(file_list) > 1:
                # Sort by timestamp descending
                file_list.sort(key=lambda x: x["timestamp"], reverse=True)
                # Keep the first (most recent)
                kept.append(file_list[0]["filename"])
                # Remove the rest
                for f in file_list[1:]:
                    try:
                        os.remove(f["path"])
                        removed.append(f["filename"])
                        # Also clean up from UPLOAD_STATUS
                        with UPLOAD_STATUS_LOCK:
                            if f["filename"] in UPLOAD_STATUS:
                                del UPLOAD_STATUS[f["filename"]]
                                _save_upload_status()
                        logger.info(f"Removed duplicate: {f['filename']}")
                    except Exception as e:
                        logger.error(f"Failed to remove {f['filename']}: {e}")
            else:
                kept.append(file_list[0]["filename"])
        
        return {
            "status": "success",
            "removed_count": len(removed),
            "kept_count": len(kept),
            "removed_files": removed,
            "message": f"Removed {len(removed)} duplicate files, kept {len(kept)} unique files"
        }
    except Exception as e:
        logger.error(f"Error cleaning up duplicates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error cleaning up duplicates: {str(e)}")


@router.post("/upload/reindex/{file_id}")
async def reindex_file(file_id: str):
    """Trigger reindexing of an existing uploaded file. Runs in background and updates UPLOAD_STATUS."""
    file_path = os.path.join(settings.UPLOAD_DIR, file_id)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")

    def _bg_reindex(path: str, fid: str):
        try:
            with UPLOAD_STATUS_LOCK:
                UPLOAD_STATUS.setdefault(fid, {})
                UPLOAD_STATUS[fid]["status"] = "indexing"
                UPLOAD_STATUS[fid]["message"] = "Manual reindexing started"
                UPLOAD_STATUS[fid]["attempts"] = 0
                _save_upload_status()

            res = index_file(path, file_id=fid)
            with UPLOAD_STATUS_LOCK:
                UPLOAD_STATUS[fid]["debug"] = res
                if res.get("status") == "success":
                    UPLOAD_STATUS[fid]["status"] = "indexed"
                    UPLOAD_STATUS[fid]["message"] = f"Indexed {res.get('indexed', 0)} chunks"
                else:
                    UPLOAD_STATUS[fid]["status"] = "error"
                    UPLOAD_STATUS[fid]["message"] = res.get("message", "Indexing failed")
                _save_upload_status()
        except Exception as e:
            with UPLOAD_STATUS_LOCK:
                UPLOAD_STATUS[fid] = {"status": "error", "message": str(e), "debug": {"exception": str(e)}, "attempts": UPLOAD_STATUS.get(fid, {}).get("attempts", 0) + 1}
                _save_upload_status()

    try:
        threading.Thread(target=_bg_reindex, args=(file_path, file_id), daemon=True).start()
    except Exception:
        # fallback synchronous
        _bg_reindex(file_path, file_id)

    return {"status": "started", "file_id": file_id, "message": "Reindexing started in background"}


@router.delete("/upload/file/{file_id}")
async def delete_file(file_id: str):
    """
    Delete an uploaded file and remove it from the vector database and UPLOAD_STATUS.
    
    Args:
        file_id: File identifier (filename)
        
    Returns:
        dict: Deletion status
    """
    file_path = os.path.join(settings.UPLOAD_DIR, file_id)
    
    # Delete from vector DB
    try:
        result = delete_file_from_chroma(file_id)
        logger.info(f"Deleted vectors for {file_id}: {result}")
    except Exception as e:
        logger.error(f"Error deleting vectors for {file_id}: {e}")
    
    # Delete physical file
    deleted_file = False
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            deleted_file = True
            logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
    
    # Remove from UPLOAD_STATUS
    with UPLOAD_STATUS_LOCK:
        if file_id in UPLOAD_STATUS:
            del UPLOAD_STATUS[file_id]
            _save_upload_status()
    
    if not deleted_file:
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")
    
    return {
        "status": "success",
        "file_id": file_id,
        "message": "File deleted successfully"
    }


@router.delete("/upload/clear-all")
async def clear_all_files():
    """
    Nuclear option: delete all uploaded files and clear the entire vector database.
    
    Returns:
        dict: Summary of cleared files and vectors
    """
    try:
        # Clear vector DB
        result = clear_all_chroma()
        logger.info(f"Cleared vector database: {result}")
        
        # Delete all files from upload directory
        deleted_count = 0
        for filename in os.listdir(settings.UPLOAD_DIR):
            file_path = os.path.join(settings.UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete {file_path}: {e}")
        
        # Clear UPLOAD_STATUS
        with UPLOAD_STATUS_LOCK:
            UPLOAD_STATUS.clear()
            _save_upload_status()
        
        return {
            "status": "success",
            "files_deleted": deleted_count,
            "vectors_cleared": result.get("status") == "success",
            "message": f"Cleared {deleted_count} files and reset vector database"
        }
        
    except Exception as e:
        logger.error(f"Error clearing all files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing files: {str(e)}")
