"""Simple OCR tool adapter.

Provides `get_ocr_tool()` returning a callable compatible with Executor.
This is a lightweight mock/adapter used when `USE_MOCKS=True`.
"""
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class MockOCR:
    def process(self, input_data: str) -> dict:
        # In real implementation, input_data would be a file path or bytes
        logger.info("Mock OCR processing invoked")
        return {"status": "success", "text": f"Mocked OCR output for: {input_data[:100]}"}


def get_ocr_tool() -> Callable[[str], dict]:
    """Return a callable that accepts a single string (action or file reference).

    The returned callable has the signature used by Executor when routing OCR tasks.
    """
    ocr = MockOCR()

    def _call(action: str) -> dict:
        return ocr.process(action)

    return _call
"""
OCR Tool - Extract text from images
Supports multiple image formats with preprocessing for better accuracy
"""
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class OCRTool:
    """Tool for extracting text from images using Tesseract OCR."""
    
    def __init__(self, languages: Optional[List[str]] = None):
        """
        Initialize the OCR tool.
        
        Args:
            languages: List of language codes for Tesseract (default: ['eng', 'spa'])
        """
        self.languages = languages or ['eng', 'spa']
        self.lang_string = '+'.join(self.languages)
        logger.info(f"OCRTool initialized with languages: {self.lang_string}")
    
    def extract_text_from_image(
        self,
        image_path: str,
        preprocess: bool = True,
        config: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract text from an image file.
        
        Args:
            image_path: Path to the image file
            preprocess: Whether to apply preprocessing for better accuracy
            config: Custom Tesseract config string
            
        Returns:
            Dict with status, text, and confidence
        """
        try:
            from PIL import Image
            import pytesseract
        except ImportError:
            logger.error("PIL or pytesseract not installed")
            return {
                "status": "error",
                "message": "Required libraries not installed. Run: pip install pillow pytesseract"
            }
        
        try:
            if not os.path.exists(image_path):
                return {
                    "status": "error",
                    "message": f"Image file not found: {image_path}"
                }
            
            # Load image
            image = Image.open(image_path)
            
            # Preprocess if requested
            if preprocess:
                image = self._preprocess_image(image)
            
            # Default config for better accuracy
            if config is None:
                config = '--oem 3 --psm 6'  # OEM 3: Default, PSM 6: Uniform block of text
            
            # Extract text
            text = pytesseract.image_to_string(
                image,
                lang=self.lang_string,
                config=config
            )
            
            # Get confidence data
            try:
                data = pytesseract.image_to_data(image, lang=self.lang_string, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            except Exception:
                avg_confidence = None
            
            logger.info(f"OCR completed for {image_path}. Text length: {len(text)}, Confidence: {avg_confidence}")
            
            return {
                "status": "success",
                "text": text.strip(),
                "confidence": avg_confidence,
                "char_count": len(text.strip()),
                "word_count": len(text.strip().split()),
                "message": "Text extracted successfully"
            }
            
        except Exception as e:
            logger.exception(f"Error during OCR: {e}")
            return {
                "status": "error",
                "message": f"OCR failed: {str(e)}"
            }
    
    def _preprocess_image(self, image: 'Image') -> 'Image':
        """
        Preprocess image for better OCR accuracy.
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image
        """
        try:
            from PIL import ImageEnhance, ImageFilter
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too small (OCR works better on larger images)
            width, height = image.size
            if width < 1000 or height < 1000:
                scale = max(1000 / width, 1000 / height)
                new_size = (int(width * scale), int(height * scale))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to grayscale
            image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Sharpen
            image = image.filter(ImageFilter.SHARPEN)
            
            # Denoise (optional - can help with noisy images)
            # image = image.filter(ImageFilter.MedianFilter(size=3))
            
            logger.debug("Image preprocessing completed")
            return image
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}. Using original image.")
            return image
    
    def batch_extract(
        self,
        image_paths: List[str],
        preprocess: bool = True
    ) -> Dict[str, Any]:
        """
        Extract text from multiple images.
        
        Args:
            image_paths: List of image file paths
            preprocess: Whether to preprocess images
            
        Returns:
            Dict with results for each image
        """
        results = {}
        total_success = 0
        total_fail = 0
        
        for image_path in image_paths:
            result = self.extract_text_from_image(image_path, preprocess)
            filename = os.path.basename(image_path)
            results[filename] = result
            
            if result["status"] == "success":
                total_success += 1
            else:
                total_fail += 1
        
        logger.info(f"Batch OCR completed: {total_success} success, {total_fail} failed")
        
        return {
            "status": "success",
            "results": results,
            "summary": {
                "total": len(image_paths),
                "success": total_success,
                "failed": total_fail
            }
        }
    
    def extract_text_with_layout(
        self,
        image_path: str,
        preprocess: bool = True
    ) -> Dict[str, Any]:
        """
        Extract text with layout information (bounding boxes, confidence per word).
        
        Args:
            image_path: Path to the image file
            preprocess: Whether to preprocess the image
            
        Returns:
            Dict with detailed OCR results including layout
        """
        try:
            from PIL import Image
            import pytesseract
        except ImportError:
            return {
                "status": "error",
                "message": "Required libraries not installed"
            }
        
        try:
            if not os.path.exists(image_path):
                return {
                    "status": "error",
                    "message": f"Image file not found: {image_path}"
                }
            
            image = Image.open(image_path)
            
            if preprocess:
                image = self._preprocess_image(image)
            
            # Get detailed data
            data = pytesseract.image_to_data(
                image,
                lang=self.lang_string,
                output_type=pytesseract.Output.DICT
            )
            
            # Parse results
            words = []
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                if int(data['conf'][i]) > 0:  # Only include detected text
                    words.append({
                        "text": data['text'][i],
                        "confidence": int(data['conf'][i]),
                        "bbox": {
                            "x": data['left'][i],
                            "y": data['top'][i],
                            "width": data['width'][i],
                            "height": data['height'][i]
                        },
                        "block": data['block_num'][i],
                        "paragraph": data['par_num'][i],
                        "line": data['line_num'][i]
                    })
            
            # Reconstruct full text
            full_text = " ".join([w["text"] for w in words if w["text"].strip()])
            
            # Calculate average confidence
            confidences = [w["confidence"] for w in words]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                "status": "success",
                "text": full_text,
                "words": words,
                "word_count": len(words),
                "avg_confidence": avg_confidence,
                "message": "Layout analysis completed"
            }
            
        except Exception as e:
            logger.exception(f"Error during layout OCR: {e}")
            return {
                "status": "error",
                "message": f"Layout OCR failed: {str(e)}"
            }


# Singleton instance
_ocr_instance = None

def get_ocr_tool() -> OCRTool:
    """Get or create the OCR tool singleton."""
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = OCRTool()
    return _ocr_instance
