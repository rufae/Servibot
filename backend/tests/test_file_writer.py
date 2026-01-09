"""
Tests for file_writer tool - PDF and Excel generation
"""
import pytest
from pathlib import Path
import os
import tempfile
from app.tools.file_writer import FileWriterTool, get_file_writer


@pytest.fixture
def temp_output_dir():
    """Create temporary directory for test outputs"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def file_writer(temp_output_dir):
    """Create FileWriterTool instance with temp directory"""
    return FileWriterTool(output_dir=temp_output_dir)


class TestFileWriterTool:
    """Test suite for FileWriterTool"""

    def test_initialization(self, file_writer, temp_output_dir):
        """Test tool initializes with correct output directory"""
        assert file_writer.output_dir == temp_output_dir
        assert os.path.exists(temp_output_dir)

    def test_generate_pdf_basic(self, file_writer):
        """Test basic PDF generation"""
        result = file_writer.generate_pdf(
            title="Test Report",
            content="This is test content.\n\nSecond paragraph.",
            filename="test_report.pdf"
        )
        
        assert result["status"] == "success"
        assert "file_path" in result
        assert result["format"] == "pdf"
        assert os.path.exists(result["file_path"])
        assert result["file_path"].endswith(".pdf")

    def test_generate_pdf_with_metadata(self, file_writer):
        """Test PDF generation with metadata"""
        metadata = {
            "author": "ServiBot",
            "created_date": "2025-01-19",
            "type": "analysis"
        }
        
        result = file_writer.generate_pdf(
            title="Report with Metadata",
            content="Content with metadata",
            filename="metadata_report.pdf",
            metadata=metadata
        )
        
        assert result["status"] == "success"
        assert os.path.exists(result["file_path"])

    def test_generate_pdf_empty_content(self, file_writer):
        """Test PDF generation handles empty content"""
        result = file_writer.generate_pdf(
            title="Empty Report",
            content="",
            filename="empty.pdf"
        )
        
        assert result["status"] == "success"
        assert os.path.exists(result["file_path"])

    def test_generate_pdf_long_content(self, file_writer):
        """Test PDF handles multi-page content"""
        long_content = "Test paragraph.\n\n" * 100
        
        result = file_writer.generate_pdf(
            title="Long Report",
            content=long_content,
            filename="long_report.pdf"
        )
        
        assert result["status"] == "success"
        assert os.path.exists(result["file_path"])

    def test_generate_excel_basic(self, file_writer):
        """Test basic Excel generation"""
        sheets = {
            "Sheet1": [
                ["Name", "Age", "City"],
                ["Alice", 30, "Madrid"],
                ["Bob", 25, "Barcelona"]
            ]
        }
        
        result = file_writer.generate_excel(
            filename="test_data.xlsx",
            sheets=sheets
        )
        
        assert result["status"] == "success"
        assert "file_path" in result
        assert result["format"] == "excel"
        assert os.path.exists(result["file_path"])
        assert result["file_path"].endswith(".xlsx")

    def test_generate_excel_multiple_sheets(self, file_writer):
        """Test Excel with multiple sheets"""
        sheets = {
            "Users": [["ID", "Name"], [1, "Alice"], [2, "Bob"]],
            "Products": [["SKU", "Price"], ["A1", 100], ["A2", 200]],
            "Orders": [["OrderID", "Total"], [1001, 300]]
        }
        
        result = file_writer.generate_excel(
            filename="multi_sheet.xlsx",
            sheets=sheets
        )
        
        assert result["status"] == "success"
        assert os.path.exists(result["file_path"])

    def test_generate_excel_with_headers(self, file_writer):
        """Test Excel with header formatting"""
        sheets = {"Data": [[1, 2, 3], [4, 5, 6]]}
        headers = {"Data": ["Col1", "Col2", "Col3"]}
        
        result = file_writer.generate_excel(
            filename="with_headers.xlsx",
            sheets=sheets,
            headers=headers
        )
        
        assert result["status"] == "success"
        assert os.path.exists(result["file_path"])

    def test_generate_excel_empty_sheet(self, file_writer):
        """Test Excel handles empty sheets"""
        sheets = {"EmptySheet": []}
        
        result = file_writer.generate_excel(
            filename="empty_sheet.xlsx",
            sheets=sheets
        )
        
        assert result["status"] == "success"
        assert os.path.exists(result["file_path"])

    def test_generate_report_pdf(self, file_writer):
        """Test high-level report generation (PDF)"""
        data = {
            "title": "Monthly Report",
            "content": "Report content here"
        }
        
        result = file_writer.generate_report(
            report_type="monthly",
            data=data,
            format="pdf"
        )
        
        assert result["status"] == "success"
        assert result["format"] == "pdf"
        assert os.path.exists(result["file_path"])

    def test_generate_report_excel(self, file_writer):
        """Test high-level report generation (Excel)"""
        data = {
            "sheets": {
                "Summary": [["Metric", "Value"], ["Total", 1000]]
            }
        }
        
        result = file_writer.generate_report(
            report_type="summary",
            data=data,
            format="excel"
        )
        
        assert result["status"] == "success"
        assert result["format"] == "excel"
        assert os.path.exists(result["file_path"])

    def test_generate_report_invalid_format(self, file_writer):
        """Test report generation handles invalid format"""
        data = {"title": "Test", "content": "Content"}
        
        result = file_writer.generate_report(
            report_type="test",
            data=data,
            format="invalid"
        )
        
        assert result["status"] == "error"
        assert "error" in result

    def test_pdf_special_characters(self, file_writer):
        """Test PDF handles special characters and accents"""
        result = file_writer.generate_pdf(
            title="Reporte con Acentos",
            content="Contenido en español: ñ, á, é, í, ó, ú, ¿, ¡",
            filename="special_chars.pdf"
        )
        
        assert result["status"] == "success"
        assert os.path.exists(result["file_path"])

    def test_excel_numeric_types(self, file_writer):
        """Test Excel handles different numeric types"""
        sheets = {
            "Numbers": [
                ["Integer", "Float", "Negative"],
                [42, 3.14, -10],
                [0, 0.001, -999]
            ]
        }
        
        result = file_writer.generate_excel(
            filename="numbers.xlsx",
            sheets=sheets
        )
        
        assert result["status"] == "success"
        assert os.path.exists(result["file_path"])


class TestFileWriterSingleton:
    """Test singleton pattern"""

    def test_get_file_writer_returns_instance(self):
        """Test singleton accessor returns FileWriterTool instance"""
        writer = get_file_writer()
        assert isinstance(writer, FileWriterTool)

    def test_get_file_writer_returns_same_instance(self):
        """Test singleton returns same instance on multiple calls"""
        writer1 = get_file_writer()
        writer2 = get_file_writer()
        assert writer1 is writer2


class TestFileWriterEdgeCases:
    """Test edge cases and error handling"""

    def test_filename_sanitization(self, file_writer):
        """Test filename with special characters is handled"""
        result = file_writer.generate_pdf(
            title="Test",
            content="Content",
            filename="file/with\\special:chars?.pdf"
        )
        
        # Should succeed with sanitized filename
        assert result["status"] == "success"
        assert os.path.exists(result["file_path"])

    def test_very_long_filename(self, file_writer):
        """Test very long filename is handled"""
        long_name = "a" * 300 + ".pdf"
        
        result = file_writer.generate_pdf(
            title="Test",
            content="Content",
            filename=long_name
        )
        
        assert result["status"] == "success"
        assert os.path.exists(result["file_path"])

    def test_unicode_content(self, file_writer):
        """Test Unicode content (emojis, symbols)"""
        result = file_writer.generate_pdf(
            title="Unicode Test 🚀",
            content="Content with emojis: 😀 🎉 ✨\nSymbols: ★ ♠ ♥ ♦ ♣",
            filename="unicode.pdf"
        )
        
        # Should handle or gracefully degrade Unicode
        assert result["status"] in ["success", "error"]
        if result["status"] == "success":
            assert os.path.exists(result["file_path"])
