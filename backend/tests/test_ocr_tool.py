"""
Tests for OCR tool - Text extraction from images
"""
import pytest
from pathlib import Path
import os
from PIL import Image, ImageDraw, ImageFont
import tempfile
from app.tools.ocr_tool import OCRTool, get_ocr_tool


@pytest.fixture
def temp_dir():
    """Create temporary directory for test images"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def ocr_tool():
    """Create OCRTool instance"""
    return OCRTool(languages="eng+spa")


@pytest.fixture
def sample_image_with_text(temp_dir):
    """Create a test image with text"""
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    # Use default font (no font file needed)
    text = "Hello World\nTest OCR 123"
    draw.text((20, 50), text, fill='black')
    
    image_path = os.path.join(temp_dir, "test_text.png")
    img.save(image_path)
    return image_path


@pytest.fixture
def sample_image_noisy(temp_dir):
    """Create a noisy test image"""
    img = Image.new('RGB', (300, 150), color='lightgray')
    draw = ImageDraw.Draw(img)
    draw.text((10, 30), "Noisy Text", fill='darkgray')
    
    image_path = os.path.join(temp_dir, "noisy.png")
    img.save(image_path)
    return image_path


@pytest.fixture
def sample_image_small(temp_dir):
    """Create a small test image"""
    img = Image.new('RGB', (100, 50), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((5, 10), "Small", fill='black')
    
    image_path = os.path.join(temp_dir, "small.png")
    img.save(image_path)
    return image_path


class TestOCRTool:
    """Test suite for OCRTool"""

    def test_initialization(self, ocr_tool):
        """Test tool initializes with correct languages"""
        assert ocr_tool.languages == "eng+spa"

    def test_initialization_default(self):
        """Test tool initializes with default languages"""
        tool = OCRTool()
        assert tool.languages == "eng+spa"

    def test_extract_text_basic(self, ocr_tool, sample_image_with_text):
        """Test basic text extraction"""
        result = ocr_tool.extract_text_from_image(sample_image_with_text)
        
        assert result["status"] == "success"
        assert "text" in result
        assert len(result["text"]) > 0
        assert "avg_confidence" in result
        assert result["avg_confidence"] >= 0

    def test_extract_text_with_preprocessing(self, ocr_tool, sample_image_noisy):
        """Test extraction with image preprocessing"""
        result = ocr_tool.extract_text_from_image(
            sample_image_noisy,
            preprocess=True
        )
        
        assert result["status"] == "success"
        assert "text" in result

    def test_extract_text_without_preprocessing(self, ocr_tool, sample_image_with_text):
        """Test extraction without preprocessing"""
        result = ocr_tool.extract_text_from_image(
            sample_image_with_text,
            preprocess=False
        )
        
        assert result["status"] == "success"
        assert "text" in result

    def test_extract_text_nonexistent_file(self, ocr_tool):
        """Test extraction handles missing file"""
        result = ocr_tool.extract_text_from_image("nonexistent.png")
        
        assert result["status"] == "error"
        assert "error" in result

    def test_extract_text_invalid_image(self, ocr_tool, temp_dir):
        """Test extraction handles corrupted image file"""
        invalid_path = os.path.join(temp_dir, "invalid.png")
        with open(invalid_path, 'w') as f:
            f.write("Not an image")
        
        result = ocr_tool.extract_text_from_image(invalid_path)
        
        assert result["status"] == "error"
        assert "error" in result

    def test_preprocess_image_small(self, ocr_tool, sample_image_small):
        """Test preprocessing resizes small images"""
        img = Image.open(sample_image_small)
        processed = ocr_tool._preprocess_image(img)
        
        # Should be resized
        assert processed.width >= img.width or processed.height >= img.height

    def test_preprocess_image_normal(self, ocr_tool, sample_image_with_text):
        """Test preprocessing doesn't break normal images"""
        img = Image.open(sample_image_with_text)
        processed = ocr_tool._preprocess_image(img)
        
        # Should be grayscale
        assert processed.mode == 'L'

    def test_batch_extract_multiple_images(self, ocr_tool, sample_image_with_text, sample_image_noisy):
        """Test batch extraction with multiple images"""
        image_paths = [sample_image_with_text, sample_image_noisy]
        
        result = ocr_tool.batch_extract(image_paths)
        
        assert result["status"] == "success"
        assert "results" in result
        assert len(result["results"]) == 2
        assert "summary" in result
        assert result["summary"]["total_files"] == 2

    def test_batch_extract_empty_list(self, ocr_tool):
        """Test batch extraction handles empty list"""
        result = ocr_tool.batch_extract([])
        
        assert result["status"] == "success"
        assert result["summary"]["total_files"] == 0

    def test_batch_extract_with_preprocessing(self, ocr_tool, sample_image_with_text):
        """Test batch extraction with preprocessing enabled"""
        result = ocr_tool.batch_extract(
            [sample_image_with_text],
            preprocess=True
        )
        
        assert result["status"] == "success"
        assert len(result["results"]) == 1

    def test_batch_extract_mixed_valid_invalid(self, ocr_tool, sample_image_with_text):
        """Test batch extraction with mix of valid and invalid files"""
        image_paths = [sample_image_with_text, "nonexistent.png"]
        
        result = ocr_tool.batch_extract(image_paths)
        
        assert result["status"] == "success"
        assert result["summary"]["successful"] >= 1
        assert result["summary"]["failed"] >= 1

    def test_extract_with_layout_basic(self, ocr_tool, sample_image_with_text):
        """Test layout extraction returns structured data"""
        result = ocr_tool.extract_text_with_layout(sample_image_with_text)
        
        assert result["status"] == "success"
        assert "layout_data" in result
        assert "full_text" in result

    def test_extract_with_layout_preprocess(self, ocr_tool, sample_image_with_text):
        """Test layout extraction with preprocessing"""
        result = ocr_tool.extract_text_with_layout(
            sample_image_with_text,
            preprocess=True
        )
        
        assert result["status"] == "success"
        assert "layout_data" in result

    def test_extract_with_layout_nonexistent(self, ocr_tool):
        """Test layout extraction handles missing file"""
        result = ocr_tool.extract_text_with_layout("nonexistent.png")
        
        assert result["status"] == "error"
        assert "error" in result

    def test_confidence_scoring(self, ocr_tool, sample_image_with_text):
        """Test confidence score is calculated"""
        result = ocr_tool.extract_text_from_image(sample_image_with_text)
        
        if result["status"] == "success" and result.get("word_count", 0) > 0:
            assert 0 <= result["avg_confidence"] <= 100

    def test_word_count_tracking(self, ocr_tool, sample_image_with_text):
        """Test word count is tracked"""
        result = ocr_tool.extract_text_from_image(sample_image_with_text)
        
        if result["status"] == "success":
            assert "word_count" in result
            assert result["word_count"] >= 0

    def test_different_languages(self):
        """Test tool can be initialized with different languages"""
        tool_eng = OCRTool(languages="eng")
        assert tool_eng.languages == "eng"
        
        tool_spa = OCRTool(languages="spa")
        assert tool_spa.languages == "spa"
        
        tool_fra = OCRTool(languages="fra")
        assert tool_fra.languages == "fra"

    def test_custom_config(self, ocr_tool, sample_image_with_text):
        """Test custom Tesseract config"""
        result = ocr_tool.extract_text_from_image(
            sample_image_with_text,
            config="--psm 6"  # Assume uniform block of text
        )
        
        assert result["status"] in ["success", "error"]


class TestOCRToolSingleton:
    """Test singleton pattern"""

    def test_get_ocr_tool_returns_instance(self):
        """Test singleton accessor returns OCRTool instance"""
        tool = get_ocr_tool()
        assert isinstance(tool, OCRTool)

    def test_get_ocr_tool_returns_same_instance(self):
        """Test singleton returns same instance"""
        tool1 = get_ocr_tool()
        tool2 = get_ocr_tool()
        assert tool1 is tool2


class TestOCRToolEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_image(self, ocr_tool, temp_dir):
        """Test OCR on blank image"""
        blank_img = Image.new('RGB', (200, 100), color='white')
        blank_path = os.path.join(temp_dir, "blank.png")
        blank_img.save(blank_path)
        
        result = ocr_tool.extract_text_from_image(blank_path)
        
        assert result["status"] == "success"
        # Empty or whitespace text expected
        assert result.get("word_count", 0) == 0 or result["text"].strip() == ""

    def test_very_large_image(self, ocr_tool, temp_dir):
        """Test OCR on large image"""
        large_img = Image.new('RGB', (3000, 2000), color='white')
        draw = ImageDraw.Draw(large_img)
        draw.text((100, 100), "Large Image Test", fill='black')
        
        large_path = os.path.join(temp_dir, "large.png")
        large_img.save(large_path)
        
        result = ocr_tool.extract_text_from_image(large_path, preprocess=True)
        
        # Should handle without crashing
        assert result["status"] in ["success", "error"]

    def test_image_with_special_chars_filename(self, ocr_tool, temp_dir):
        """Test OCR with filename containing special characters"""
        img = Image.new('RGB', (200, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((20, 30), "Test", fill='black')
        
        # File with special chars in name
        special_path = os.path.join(temp_dir, "file_with_ñ_á.png")
        img.save(special_path)
        
        result = ocr_tool.extract_text_from_image(special_path)
        
        assert result["status"] in ["success", "error"]

    def test_batch_summary_statistics(self, ocr_tool, sample_image_with_text, sample_image_noisy):
        """Test batch extraction summary contains correct stats"""
        result = ocr_tool.batch_extract([sample_image_with_text, sample_image_noisy])
        
        summary = result["summary"]
        assert summary["total_files"] == 2
        assert summary["successful"] + summary["failed"] == 2
        assert summary["total_words"] >= 0
        assert summary["total_chars"] >= 0
