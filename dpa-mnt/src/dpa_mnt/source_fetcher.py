"""Source fetching and content extraction for dpa_mnt.

DPA sources are primarily web URLs (from lux_source_log.source_url).
Fallback to S3 HTTP URLs via lux_file_log.file_url.
"""

from typing import Optional
from io import BytesIO
import httpx
import os

from .models import SourceResult
from .storage import ReviewStorage


class SourceFetcher:
    """Fetches and extracts official sources from URLs or S3 HTTP paths.

    Priority for DPA: URL first (most sources are web URLs), S3 HTTP fallback.
    Supports PDF text extraction and HTML parsing.
    """

    def __init__(self, storage: Optional[ReviewStorage] = None):
        self.storage = storage or ReviewStorage()

    def _extract_pdf_text(self, pdf_bytes: bytes) -> str:
        try:
            from pypdf import PdfReader
            reader = PdfReader(BytesIO(pdf_bytes))
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text())
            full_text = "\n\n".join(text_parts)
            if len(full_text.strip()) < 100:
                return "[PDF extraction failed - likely scanned document. Refer to source URL.]"
            return full_text
        except Exception as e:
            return f"[PDF extraction error: {e}]"

    def _extract_html_text(self, html_bytes: bytes) -> str:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_bytes, 'lxml')
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            return text
        except Exception as e:
            return f"[HTML extraction error: {e}]"

    def _get_content_type(self, url: str) -> str:
        url_lower = url.lower()
        if url_lower.endswith('.pdf'):
            return "pdf"
        elif url_lower.endswith(('.html', '.htm')):
            return "html"
        else:
            return "html"  # Default to HTML for web URLs

    async def get_source(
        self,
        intervention_id: int,
        event_id: int,
        source_data: dict,
        fetch_content: bool = True
    ) -> SourceResult:
        """Retrieve official source for a DPA event.

        Priority: source_url first (web URL), then file_url (S3 HTTP).

        Args:
            intervention_id: Intervention ID (for storage path)
            event_id: Event ID
            source_data: Source dict with source_url and optionally file_url
            fetch_content: Whether to fetch and extract content

        Returns:
            SourceResult with source type, URL, and optional content
        """
        source_url = source_data.get('source_url')
        file_url = source_data.get('file_url')

        # Use source_url as primary, file_url as fallback
        url = source_url or file_url
        if not url:
            raise ValueError(f"No source URL available for event {event_id}")

        source_type = "url"
        content_type = self._get_content_type(url)

        if not fetch_content:
            return SourceResult(
                source_type=source_type,
                source_url=url,
                content=None,
                content_type=content_type
            )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                url_bytes = response.content

            # Detect content type from response headers if available
            resp_ct = response.headers.get('content-type', '')
            if 'pdf' in resp_ct:
                content_type = "pdf"
            elif 'html' in resp_ct:
                content_type = "html"

            # Save to persistent storage
            self.storage.save_source(
                intervention_id=intervention_id,
                event_id=event_id,
                content=url_bytes,
                content_type=content_type,
                source_url=url
            )

            # Extract text based on type
            if content_type == "pdf":
                content = self._extract_pdf_text(url_bytes)
            elif content_type == "html":
                content = self._extract_html_text(url_bytes)
            else:
                content = url_bytes.decode('utf-8', errors='ignore')

            return SourceResult(
                source_type=source_type,
                source_url=url,
                content=content,
                content_type=content_type
            )

        except Exception as e:
            return SourceResult(
                source_type=source_type,
                source_url=url,
                content=f"[URL fetch error: {e}]",
                content_type=content_type
            )
