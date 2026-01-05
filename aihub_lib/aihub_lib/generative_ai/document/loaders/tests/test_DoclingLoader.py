"""Tests for DoclingLoader PDF preprocessing functionality."""

import logging
from io import BytesIO

import pytest
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

from aihub_lib.generative_ai.document.loaders.DoclingLoader import (
    A4_HEIGHT_POINTS,
    A4_WIDTH_POINTS,
    _fix_pdf_mediabox,
)


def _create_pdf_with_mediabox(width: int, height: int, num_pages: int = 1) -> bytes:
    """
    Create a PDF with specified mediabox dimensions.

    ### Why This Helper?
    Tests need PDFs with specific mediabox configurations to verify fix behavior.
    Creating them programmatically ensures consistent, reproducible test data.
    """
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=width, height=height)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def _create_pdf_with_missing_mediabox() -> bytes:
    """
    Create a PDF where pages have None mediabox.

    ### Why This Approach?
    pypdf doesn't allow creating pages without mediabox directly,
    so we create a valid PDF and then manually corrupt the structure.
    The _fix_pdf_mediabox function should handle this gracefully.
    """
    # Create a minimal valid PDF, then corrupt it by removing mediabox
    writer = PdfWriter()
    writer.add_blank_page(width=A4_WIDTH_POINTS, height=A4_HEIGHT_POINTS)
    output = BytesIO()
    writer.write(output)
    pdf_bytes = output.getvalue()

    # We can't easily remove mediabox from a real PDF, so we test
    # the zero-dimension case instead, which triggers the same fix path
    return pdf_bytes


class TestFixPdfMediabox:
    """Tests for _fix_pdf_mediabox PDF preprocessing function."""

    def test_pdf_with_valid_mediabox_passes_through(self) -> None:
        """Valid PDF with proper dimensions should not be modified structurally."""
        original = _create_pdf_with_mediabox(width=612, height=792)  # US Letter
        result = _fix_pdf_mediabox(original, "document.pdf")

        # Verify output is valid PDF with same page count
        reader = PdfReader(BytesIO(result))
        assert len(reader.pages) == 1
        # Original dimensions should be preserved (Letter, not A4)
        assert reader.pages[0].mediabox.width == 612
        assert reader.pages[0].mediabox.height == 792

    def test_pdf_with_zero_width_gets_a4_default(self) -> None:
        """PDF with zero-width mediabox should be fixed to A4 dimensions."""
        # Create PDF then modify to have zero width (simulating corrupted PDF)
        writer = PdfWriter()
        writer.add_blank_page(width=A4_WIDTH_POINTS, height=A4_HEIGHT_POINTS)
        # Manually set zero width
        writer.pages[0].mediabox = RectangleObject((0, 0, 0, A4_HEIGHT_POINTS))
        output = BytesIO()
        writer.write(output)
        corrupted = output.getvalue()

        result = _fix_pdf_mediabox(corrupted, "document.pdf")

        reader = PdfReader(BytesIO(result))
        assert reader.pages[0].mediabox.width == A4_WIDTH_POINTS
        assert reader.pages[0].mediabox.height == A4_HEIGHT_POINTS

    def test_pdf_with_zero_height_gets_a4_default(self) -> None:
        """PDF with zero-height mediabox should be fixed to A4 dimensions."""
        writer = PdfWriter()
        writer.add_blank_page(width=A4_WIDTH_POINTS, height=A4_HEIGHT_POINTS)
        writer.pages[0].mediabox = RectangleObject((0, 0, A4_WIDTH_POINTS, 0))
        output = BytesIO()
        writer.write(output)
        corrupted = output.getvalue()

        result = _fix_pdf_mediabox(corrupted, "document.pdf")

        reader = PdfReader(BytesIO(result))
        assert reader.pages[0].mediabox.width == A4_WIDTH_POINTS
        assert reader.pages[0].mediabox.height == A4_HEIGHT_POINTS

    def test_non_pdf_file_returns_unchanged(self) -> None:
        """Non-PDF files should pass through without modification."""
        content = b"This is a text file content"

        result = _fix_pdf_mediabox(content, "document.txt")

        assert result == content

    def test_docx_file_returns_unchanged(self) -> None:
        """DOCX files should pass through without modification."""
        content = b"PK\x03\x04fake docx content"

        result = _fix_pdf_mediabox(content, "document.docx")

        assert result == content

    def test_corrupted_pdf_returns_original_with_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Corrupted PDF should return original content and log warning."""
        corrupted_content = b"not a valid PDF at all"

        with caplog.at_level(logging.WARNING):
            result = _fix_pdf_mediabox(corrupted_content, "corrupted.pdf")

        assert result == corrupted_content
        assert "Could not preprocess PDF corrupted.pdf" in caplog.text

    def test_case_insensitive_pdf_extension(self) -> None:
        """PDF extension check should be case-insensitive."""
        original = _create_pdf_with_mediabox(width=612, height=792)

        # Test uppercase
        result_upper = _fix_pdf_mediabox(original, "document.PDF")
        reader = PdfReader(BytesIO(result_upper))
        assert len(reader.pages) == 1

        # Test mixed case
        result_mixed = _fix_pdf_mediabox(original, "document.Pdf")
        reader = PdfReader(BytesIO(result_mixed))
        assert len(reader.pages) == 1

    def test_multipage_pdf_all_pages_processed(self) -> None:
        """All pages in multi-page PDF should be checked and fixed if needed."""
        # Create 3-page PDF with valid dimensions
        writer = PdfWriter()
        for _ in range(3):
            writer.add_blank_page(width=A4_WIDTH_POINTS, height=A4_HEIGHT_POINTS)
        # Corrupt second page
        writer.pages[1].mediabox = RectangleObject((0, 0, 0, 0))
        output = BytesIO()
        writer.write(output)
        pdf_bytes = output.getvalue()

        result = _fix_pdf_mediabox(pdf_bytes, "multipage.pdf")

        reader = PdfReader(BytesIO(result))
        assert len(reader.pages) == 3
        # All pages should have valid A4 dimensions
        for page in reader.pages:
            assert page.mediabox.width == A4_WIDTH_POINTS
            assert page.mediabox.height == A4_HEIGHT_POINTS

    def test_empty_filename_with_pdf_extension(self) -> None:
        """Filename that ends with .pdf should be processed."""
        original = _create_pdf_with_mediabox(width=612, height=792)

        result = _fix_pdf_mediabox(original, ".pdf")

        reader = PdfReader(BytesIO(result))
        assert len(reader.pages) == 1

    def test_constants_have_expected_values(self) -> None:
        """Verify A4 constants match expected PostScript point values."""
        # A4: 210mm x 297mm at 72 points/inch
        # 210mm = 8.27 inches = 595.44 points ≈ 595
        # 297mm = 11.69 inches = 841.68 points ≈ 842
        assert A4_WIDTH_POINTS == 595
        assert A4_HEIGHT_POINTS == 842
