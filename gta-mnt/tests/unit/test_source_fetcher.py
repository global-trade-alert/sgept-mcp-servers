"""Unit tests for source fetcher."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from io import BytesIO

from gta_mnt.source_fetcher import SourceFetcher
from gta_mnt.models import SourceResult


@pytest.fixture
def source_fetcher():
    """Create SourceFetcher instance."""
    with patch('gta_mnt.source_fetcher.boto3.client'):
        return SourceFetcher()


def test_parse_s3_url(source_fetcher):
    """Test S3 URL parsing."""
    bucket, key = source_fetcher._parse_s3_url("s3://my-bucket/path/to/file.pdf")
    assert bucket == "my-bucket"
    assert key == "path/to/file.pdf"


def test_parse_s3_url_no_path(source_fetcher):
    """Test S3 URL parsing with no path."""
    bucket, key = source_fetcher._parse_s3_url("s3://my-bucket")
    assert bucket == "my-bucket"
    assert key == ""


def test_get_content_type_pdf(source_fetcher):
    """Test content type detection for PDF."""
    assert source_fetcher._get_content_type("document.pdf") == "pdf"
    assert source_fetcher._get_content_type("DOCUMENT.PDF") == "pdf"


def test_get_content_type_html(source_fetcher):
    """Test content type detection for HTML."""
    assert source_fetcher._get_content_type("page.html") == "html"
    assert source_fetcher._get_content_type("page.htm") == "html"


def test_get_content_type_other(source_fetcher):
    """Test content type detection for other files."""
    assert source_fetcher._get_content_type("file.txt") == "text"
    assert source_fetcher._get_content_type("unknown") == "text"


def test_extract_pdf_text_success(source_fetcher):
    """Test PDF text extraction."""
    # Create a minimal mock PDF
    with patch('pypdf.PdfReader') as mock_reader:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "This is PDF content." * 10  # Ensure > 100 chars
        mock_reader.return_value.pages = [mock_page]

        result = source_fetcher._extract_pdf_text(b"fake-pdf-bytes")

        assert "This is PDF content." in result
        assert "[PDF extraction failed" not in result


def test_extract_pdf_text_scanned_document(source_fetcher):
    """Test PDF extraction handles scanned documents."""
    with patch('pypdf.PdfReader') as mock_reader:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""  # Scanned PDF returns empty
        mock_reader.return_value.pages = [mock_page]

        result = source_fetcher._extract_pdf_text(b"fake-pdf-bytes")

        assert "[PDF extraction failed - likely scanned document" in result


def test_extract_pdf_text_error(source_fetcher):
    """Test PDF extraction handles errors gracefully."""
    with patch('pypdf.PdfReader', side_effect=Exception("Parse error")):
        result = source_fetcher._extract_pdf_text(b"fake-pdf-bytes")

        assert "[PDF extraction error:" in result


def test_extract_html_text(source_fetcher):
    """Test HTML text extraction."""
    html = b"""
    <html>
        <head><title>Test</title></head>
        <body>
            <script>alert('remove me');</script>
            <p>This is content.</p>
            <p>Another paragraph.</p>
        </body>
    </html>
    """

    result = source_fetcher._extract_html_text(html)

    assert "This is content." in result
    assert "Another paragraph." in result
    assert "alert" not in result  # Script tags removed
    assert "<p>" not in result  # HTML tags removed


@pytest.mark.asyncio
async def test_get_source_s3_file(source_fetcher):
    """Test get_source with S3 file."""
    measure_data = {
        "source_file": "s3://bucket/file.pdf",
        "source_url": None
    }

    with patch.object(source_fetcher, '_fetch_s3_file', return_value=b"PDF content bytes"):
        with patch.object(source_fetcher, '_extract_pdf_text', return_value="Extracted text"):
            result = await source_fetcher.get_source(
                state_act_id=123,
                measure_data=measure_data,
                fetch_content=True
            )

            assert isinstance(result, SourceResult)
            assert result.source_type == "file"
            assert result.source_url == "s3://bucket/file.pdf"
            assert result.content == "Extracted text"
            assert result.content_type == "pdf"


@pytest.mark.asyncio
async def test_get_source_url_fallback(source_fetcher):
    """Test get_source falls back to URL when S3 fails."""
    measure_data = {
        "source_file": None,  # No S3 file
        "source_url": "https://example.com/doc.html"
    }

    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = b"<html>HTML content</html>"
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        with patch.object(source_fetcher, '_extract_html_text', return_value="Extracted HTML"):
            result = await source_fetcher.get_source(
                state_act_id=123,
                measure_data=measure_data,
                fetch_content=True
            )

            assert result.source_type == "url"
            assert result.source_url == "https://example.com/doc.html"
            assert result.content == "Extracted HTML"


@pytest.mark.asyncio
async def test_get_source_without_fetch_content(source_fetcher):
    """Test get_source returns metadata only when fetch_content=False."""
    measure_data = {
        "source_file": "s3://bucket/file.pdf",
        "source_url": None
    }

    result = await source_fetcher.get_source(
        state_act_id=123,
        measure_data=measure_data,
        fetch_content=False
    )

    assert result.source_type == "file"
    assert result.content is None


@pytest.mark.asyncio
async def test_get_source_no_source_available(source_fetcher):
    """Test get_source raises error when no source available."""
    measure_data = {
        "source_file": None,
        "source_url": None
    }

    with pytest.raises(ValueError, match="No source available"):
        await source_fetcher.get_source(
            state_act_id=123,
            measure_data=measure_data,
            fetch_content=True
        )
