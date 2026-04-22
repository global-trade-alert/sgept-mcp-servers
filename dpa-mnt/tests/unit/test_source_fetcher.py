"""Unit tests for dpa_mnt SourceFetcher."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from dpa_mnt.source_fetcher import SourceFetcher
from dpa_mnt.models import SourceResult
from dpa_mnt.storage import ReviewStorage


@pytest.fixture
def source_fetcher(tmp_path):
    """Fetcher wired to a tmp_path-backed ReviewStorage so auto-save lands in a
    scratch directory."""
    storage = ReviewStorage(base_path=str(tmp_path))
    return SourceFetcher(storage=storage)


# ============================================================================
# Content type detection
# ============================================================================


def test_get_content_type_pdf(source_fetcher):
    assert source_fetcher._get_content_type("https://example.com/policy.pdf") == "pdf"
    assert source_fetcher._get_content_type("https://example.com/POLICY.PDF") == "pdf"


def test_get_content_type_html(source_fetcher):
    assert source_fetcher._get_content_type("https://example.com/page.html") == "html"
    assert source_fetcher._get_content_type("https://example.com/page.htm") == "html"


def test_get_content_type_default_html_for_bare_url(source_fetcher):
    # DPA sources are mostly web URLs without extensions; default to html.
    assert source_fetcher._get_content_type("https://example.com/policy") == "html"


# ============================================================================
# PDF text extraction
# ============================================================================


def test_extract_pdf_text_success(source_fetcher):
    with patch("pypdf.PdfReader") as mock_reader:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "This is DPA policy text. " * 10
        mock_reader.return_value.pages = [mock_page]

        result = source_fetcher._extract_pdf_text(b"fake-pdf-bytes")
        assert "This is DPA policy text." in result
        assert "[PDF extraction failed" not in result


def test_extract_pdf_text_scanned_returns_stub(source_fetcher):
    with patch("pypdf.PdfReader") as mock_reader:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_reader.return_value.pages = [mock_page]

        result = source_fetcher._extract_pdf_text(b"fake-pdf-bytes")
        assert "[PDF extraction failed - likely scanned document" in result


def test_extract_pdf_text_error_returns_message(source_fetcher):
    with patch("pypdf.PdfReader", side_effect=RuntimeError("bad pdf")):
        result = source_fetcher._extract_pdf_text(b"fake-pdf-bytes")
        assert "[PDF extraction error:" in result


# ============================================================================
# HTML text extraction
# ============================================================================


def test_extract_html_strips_script_and_tags(source_fetcher):
    html = b"""
    <html>
      <head><title>Policy</title></head>
      <body>
        <script>alert('drop me');</script>
        <style>body { color: red; }</style>
        <p>This is policy content.</p>
        <p>Another paragraph.</p>
      </body>
    </html>
    """
    text = source_fetcher._extract_html_text(html)
    assert "This is policy content." in text
    assert "Another paragraph." in text
    assert "alert" not in text
    assert "color: red" not in text
    assert "<p>" not in text


# ============================================================================
# get_source end-to-end (with mocked httpx)
# ============================================================================


@pytest.mark.asyncio
async def test_get_source_url_html_fetches_and_extracts(source_fetcher):
    source_data = {
        "source_url": "https://example.com/policy",
        "file_url": None,
    }

    with patch("dpa_mnt.source_fetcher.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = b"<html><body><p>HTML body</p></body></html>"
        mock_response.headers = {"content-type": "text/html; charset=utf-8"}
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await source_fetcher.get_source(
            intervention_id=777,
            event_id=501,
            source_data=source_data,
            fetch_content=True,
        )

    assert isinstance(result, SourceResult)
    assert result.source_type == "url"
    assert result.source_url == "https://example.com/policy"
    assert result.content_type == "html"
    assert "HTML body" in result.content


@pytest.mark.asyncio
async def test_get_source_file_url_fallback(source_fetcher):
    """When source_url is missing, file_url (S3 HTTP) is used."""
    source_data = {
        "source_url": None,
        "file_url": "https://s3.example.com/doc.pdf",
    }

    with patch("dpa_mnt.source_fetcher.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = b"%PDF-1.4 fake"
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        with patch.object(source_fetcher, "_extract_pdf_text", return_value="PDF body"):
            result = await source_fetcher.get_source(
                intervention_id=777,
                event_id=501,
                source_data=source_data,
                fetch_content=True,
            )

    assert result.source_url == "https://s3.example.com/doc.pdf"
    assert result.content_type == "pdf"
    assert result.content == "PDF body"


@pytest.mark.asyncio
async def test_get_source_without_fetch_returns_metadata_only(source_fetcher):
    source_data = {
        "source_url": "https://example.com/policy.pdf",
        "file_url": None,
    }
    result = await source_fetcher.get_source(
        intervention_id=777,
        event_id=501,
        source_data=source_data,
        fetch_content=False,
    )
    assert result.content is None
    assert result.source_url == "https://example.com/policy.pdf"


@pytest.mark.asyncio
async def test_get_source_raises_when_no_url(source_fetcher):
    source_data = {"source_url": None, "file_url": None}
    with pytest.raises(ValueError, match="No source URL available"):
        await source_fetcher.get_source(
            intervention_id=777,
            event_id=501,
            source_data=source_data,
            fetch_content=True,
        )


@pytest.mark.asyncio
async def test_get_source_persists_to_disk(source_fetcher, tmp_path):
    source_data = {
        "source_url": "https://example.com/policy",
        "file_url": None,
    }

    with patch("dpa_mnt.source_fetcher.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = b"<html>POLICY</html>"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        await source_fetcher.get_source(
            intervention_id=777,
            event_id=501,
            source_data=source_data,
            fetch_content=True,
        )

    # The auto-save drops into the ReviewStorage base_path with the evt- prefix.
    saved_file = tmp_path / "777" / "evt-501-source.html"
    assert saved_file.exists()
    assert saved_file.read_bytes() == b"<html>POLICY</html>"

    url_meta = tmp_path / "777" / "evt-501-source-url.txt"
    assert url_meta.exists()
    assert url_meta.read_text() == "https://example.com/policy"
