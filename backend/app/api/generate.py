"""
File Generation API
Endpoints for generating PDF and Excel files
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import os

from app.tools.file_writer import get_file_writer

logger = logging.getLogger(__name__)
router = APIRouter()


class PDFRequest(BaseModel):
    """PDF generation request model."""
    title: str
    content: str
    filename: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ExcelRequest(BaseModel):
    """Excel generation request model."""
    filename: str
    sheets: Dict[str, List[List[Any]]]
    headers: Optional[Dict[str, List[str]]] = None


class ReportRequest(BaseModel):
    """Report generation request model."""
    report_type: str  # summary, detailed, custom
    data: Dict[str, Any]
    format: str = "pdf"  # pdf or excel


class FileGenerationResponse(BaseModel):
    """File generation response model."""
    status: str
    filename: Optional[str] = None
    file_url: Optional[str] = None
    message: Optional[str] = None


@router.post("/generate/pdf", response_model=FileGenerationResponse)
async def generate_pdf(request: PDFRequest):
    """
    Generate a PDF document.
    
    Args:
        request: PDF generation request
        
    Returns:
        File information and download URL
    """
    try:
        writer = get_file_writer()
        result = writer.generate_pdf(
            title=request.title,
            content=request.content,
            filename=request.filename,
            metadata=request.metadata
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        # Generate download URL
        file_url = f"/api/generate/download/{result['filename']}"
        
        return FileGenerationResponse(
            status="success",
            filename=result["filename"],
            file_url=file_url,
            message=result["message"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error generating PDF: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.post("/generate/excel", response_model=FileGenerationResponse)
async def generate_excel(request: ExcelRequest):
    """
    Generate an Excel file.
    
    Args:
        request: Excel generation request
        
    Returns:
        File information and download URL
    """
    try:
        writer = get_file_writer()
        result = writer.generate_excel(
            filename=request.filename,
            sheets=request.sheets,
            headers=request.headers
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        # Generate download URL
        file_url = f"/api/generate/download/{result['filename']}"
        
        return FileGenerationResponse(
            status="success",
            filename=result["filename"],
            file_url=file_url,
            message=result["message"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error generating Excel: {e}")
        raise HTTPException(status_code=500, detail=f"Excel generation failed: {str(e)}")


@router.post("/generate/report", response_model=FileGenerationResponse)
async def generate_report(request: ReportRequest):
    """
    Generate a formatted report (PDF or Excel).
    
    Args:
        request: Report generation request
        
    Returns:
        File information and download URL
    """
    try:
        writer = get_file_writer()
        result = writer.generate_report(
            report_type=request.report_type,
            data=request.data,
            format=request.format
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        # Generate download URL
        file_url = f"/api/generate/download/{result['filename']}"
        
        return FileGenerationResponse(
            status="success",
            filename=result["filename"],
            file_url=file_url,
            message=result["message"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/generate/download/{filename}")
async def download_generated_file(filename: str):
    """
    Download a generated file.
    
    Args:
        filename: Name of the generated file
        
    Returns:
        File download response
    """
    try:
        writer = get_file_writer()
        file_path = os.path.join(writer.output_dir, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")
        
        # Determine media type
        if filename.endswith('.pdf'):
            media_type = "application/pdf"
        elif filename.endswith('.xlsx'):
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            media_type = "application/octet-stream"
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=f"File download failed: {str(e)}")


@router.get("/generate/list")
async def list_generated_files():
    """
    List all generated files.
    
    Returns:
        List of generated files with metadata
    """
    try:
        writer = get_file_writer()
        
        if not os.path.exists(writer.output_dir):
            return {
                "status": "success",
                "files": [],
                "count": 0
            }
        
        files = []
        for filename in os.listdir(writer.output_dir):
            file_path = os.path.join(writer.output_dir, filename)
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                files.append({
                    "filename": filename,
                    "size_bytes": stat.st_size,
                    "created_at": stat.st_ctime,
                    "file_type": "pdf" if filename.endswith('.pdf') else "excel" if filename.endswith('.xlsx') else "other",
                    "download_url": f"/api/generate/download/{filename}"
                })
        
        # Sort by creation time (newest first)
        files.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "status": "success",
            "files": files,
            "count": len(files)
        }
    
    except Exception as e:
        logger.exception(f"Error listing generated files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")
