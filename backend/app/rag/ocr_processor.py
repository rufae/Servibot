"""
OCR Processor for scanned documents
Handles image-based PDFs and image files to extract text
"""

import os
import io
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging

try:
    from PIL import Image
    import pytesseract
    HAS_OCR_SUPPORT = True
except ImportError:
    HAS_OCR_SUPPORT = False

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

logger = logging.getLogger(__name__)

class OCRProcessor:
    """
    Handles OCR for scanned documents and images
    """
    
    def __init__(self, language: str = 'spa+eng'):
        """
        Initialize OCR processor
        
        Args:
            language: Tesseract language code (default: spa+eng for Spanish+English)
        """
        self.language = language
        self.has_ocr = HAS_OCR_SUPPORT
        self.has_pymupdf = HAS_PYMUPDF
        
        if not self.has_ocr:
            logger.warning("OCR support not available. Install pytesseract and Pillow.")
        
        if not self.has_pymupdf:
            logger.warning("PyMuPDF not available. PDF image extraction disabled.")
    
    def is_pdf_scanned(self, pdf_path: str) -> bool:
        """
        Detect if a PDF is primarily image-based (scanned)
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            True if PDF appears to be scanned
        """
        if not self.has_pymupdf:
            return False
        
        try:
            doc = fitz.open(pdf_path)
            
            # Check first 3 pages (or all if fewer)
            pages_to_check = min(3, len(doc))
            text_pages = 0
            image_pages = 0
            
            for page_num in range(pages_to_check):
                page = doc[page_num]
                text = page.get_text().strip()
                images = page.get_images()
                
                # If page has minimal text but has images, likely scanned
                if len(text) < 50 and len(images) > 0:
                    image_pages += 1
                elif len(text) > 50:
                    text_pages += 1
            
            doc.close()
            
            # If more than half the checked pages are image-based
            return image_pages > text_pages
            
        except Exception as e:
            logger.error(f"Error checking if PDF is scanned: {e}")
            return False
    
    def extract_text_from_image(self, image_path: str) -> str:
        """
        Extract text from a single image file using OCR
        
        Args:
            image_path: Path to image file
            
        Returns:
            Extracted text
        """
        if not self.has_ocr:
            return ""
        
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang=self.language)
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""
    
    def extract_text_from_pdf_images(self, pdf_path: str) -> str:
        """
        Extract text from all images in a PDF using OCR
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text from all pages
        """
        if not self.has_ocr or not self.has_pymupdf:
            return ""
        
        try:
            doc = fitz.open(pdf_path)
            all_text = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # First try to get existing text
                page_text = page.get_text().strip()
                
                # If minimal text, try OCR on images
                if len(page_text) < 50:
                    images = page.get_images()
                    
                    for img_index, img in enumerate(images):
                        try:
                            xref = img[0]
                            base_image = doc.extract_image(xref)
                            image_bytes = base_image["image"]
                            
                            # Convert to PIL Image
                            image = Image.open(io.BytesIO(image_bytes))
                            
                            # Perform OCR
                            ocr_text = pytesseract.image_to_string(image, lang=self.language)
                            
                            if ocr_text.strip():
                                all_text.append(f"[Página {page_num + 1} - Imagen {img_index + 1}]")
                                all_text.append(ocr_text.strip())
                                
                        except Exception as e:
                            logger.error(f"Error processing image {img_index} on page {page_num}: {e}")
                            continue
                else:
                    # Use existing text
                    all_text.append(f"[Página {page_num + 1}]")
                    all_text.append(page_text)
            
            doc.close()
            return "\n\n".join(all_text)
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF images: {e}")
            return ""
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process a file (image or PDF) and extract text with OCR if needed
        
        Args:
            file_path: Path to file
            
        Returns:
            Dict with:
                - text: Extracted text
                - ocr_used: Whether OCR was used
                - is_scanned: Whether document was detected as scanned
                - error: Error message if any
        """
        result = {
            "text": "",
            "ocr_used": False,
            "is_scanned": False,
            "error": None
        }
        
        if not os.path.exists(file_path):
            result["error"] = "File not found"
            return result
        
        file_ext = Path(file_path).suffix.lower()
        
        try:
            # Handle images
            if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']:
                if not self.has_ocr:
                    result["error"] = "OCR support not available"
                    return result
                
                text = self.extract_text_from_image(file_path)
                result["text"] = text
                result["ocr_used"] = True
                result["is_scanned"] = True
                
            # Handle PDFs
            elif file_ext == '.pdf':
                is_scanned = self.is_pdf_scanned(file_path)
                result["is_scanned"] = is_scanned
                
                if is_scanned:
                    if not self.has_ocr:
                        result["error"] = "PDF appears to be scanned but OCR support not available"
                        return result
                    
                    text = self.extract_text_from_pdf_images(file_path)
                    result["text"] = text
                    result["ocr_used"] = True
                else:
                    # Use standard text extraction (handled by ingest.py)
                    result["text"] = ""  # Let ingest.py handle it
                    result["ocr_used"] = False
                    
            else:
                result["error"] = f"Unsupported file type: {file_ext}"
                
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            result["error"] = str(e)
        
        return result
    
    def get_ocr_status(self) -> Dict[str, Any]:
        """
        Get OCR support status and configuration
        
        Returns:
            Dict with OCR status information
        """
        status = {
            "available": self.has_ocr and self.has_pymupdf,
            "language": self.language if self.has_ocr else None,
            "tesseract_available": self.has_ocr,
            "pymupdf_available": self.has_pymupdf
        }
        
        if self.has_ocr:
            try:
                tesseract_version = pytesseract.get_tesseract_version()
                status["tesseract_version"] = str(tesseract_version)
            except:
                status["tesseract_version"] = "Unknown"
        
        return status


# Singleton instance
_ocr_processor_instance: Optional[OCRProcessor] = None

def get_ocr_processor(language: str = 'spa+eng') -> OCRProcessor:
    """
    Get or create OCR processor singleton
    
    Args:
        language: Tesseract language code
        
    Returns:
        OCRProcessor instance
    """
    global _ocr_processor_instance
    
    if _ocr_processor_instance is None:
        _ocr_processor_instance = OCRProcessor(language=language)
    
    return _ocr_processor_instance
