"""Source fetching and content extraction for gta_mnt."""

from typing import Optional
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from io import BytesIO
import httpx
import os

from .models import SourceResult
from .storage import ReviewStorage


class SourceFetcher:
    """Fetches and extracts official sources from S3 or URLs.

    Priority: S3 archived files first, fallback to URLs.
    Supports PDF text extraction and HTML parsing.
    """

    def __init__(self, storage: Optional[ReviewStorage] = None):
        """Initialize S3 client and storage.

        Args:
            storage: ReviewStorage instance (creates new if not provided)
        """
        self.s3_client = boto3.client(
            's3',
            region_name=os.getenv('AWS_S3_REGION', 'eu-west-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.storage = storage or ReviewStorage()

    def _parse_s3_url(self, s3_url: str) -> tuple[str, str]:
        """Parse S3 URL into bucket and key.

        Args:
            s3_url: S3 URL (s3://bucket/key/path)

        Returns:
            (bucket_name, object_key)
        """
        # Remove s3:// prefix
        path = s3_url.replace("s3://", "")
        parts = path.split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""
        return bucket, key

    async def _fetch_s3_file(self, bucket: str, key: str) -> bytes:
        """Fetch file content from S3.

        Args:
            bucket: S3 bucket name
            key: Object key

        Returns:
            File content as bytes

        Raises:
            ClientError: If S3 access fails
        """
        response = self.s3_client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()

    def _extract_pdf_text(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF using pypdf.

        Args:
            pdf_bytes: PDF file content

        Returns:
            Extracted text content

        Note:
            Returns error message if extraction fails or PDF is scanned.
        """
        try:
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(pdf_bytes))
            text_parts = []

            for page in reader.pages:
                text_parts.append(page.extract_text())

            full_text = "\n\n".join(text_parts)

            # Check if extraction yielded meaningful content
            if len(full_text.strip()) < 100:
                return "[PDF extraction failed - likely scanned document. Refer to source URL.]"

            return full_text

        except Exception as e:
            return f"[PDF extraction error: {e}]"

    def _extract_html_text(self, html_bytes: bytes) -> str:
        """Extract text from HTML using BeautifulSoup.

        Args:
            html_bytes: HTML file content

        Returns:
            Extracted text content
        """
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html_bytes, 'lxml')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            return text

        except Exception as e:
            return f"[HTML extraction error: {e}]"

    def _get_content_type(self, filename: str) -> str:
        """Determine content type from filename.

        Args:
            filename: File name with extension

        Returns:
            Content type string: "pdf", "html", or "text"
        """
        filename_lower = filename.lower()
        if filename_lower.endswith('.pdf'):
            return "pdf"
        elif filename_lower.endswith(('.html', '.htm')):
            return "html"
        else:
            return "text"

    # ========================================================================
    # WS4: Get Source Implementation
    # ========================================================================

    async def get_source(
        self,
        state_act_id: int,
        measure_data: dict,
        fetch_content: bool = True,
        source_index: int = 0
    ) -> SourceResult:
        """Retrieve official source for a StateAct.

        Priority: S3 archived file first, fallback to URL.
        Extracts text from PDFs and HTML when fetch_content=True.

        Args:
            state_act_id: StateAct ID
            measure_data: Measure dict from API (contains sources list)
            fetch_content: Whether to fetch and extract content
            source_index: Which source to fetch (0-indexed, default first source)

        Returns:
            SourceResult with source type, URL, and optional content
        """
        # Get sources list from measure data
        sources = measure_data.get('sources', [])
        source_info = measure_data.get('source_info', {})
        linked_sources = source_info.get('linked_sources', sources)

        # Legacy support: check for top-level source_file/source_url
        source_file = measure_data.get("source_file")
        source_url = measure_data.get("source_url")

        # If we have a sources list, use it
        if linked_sources and source_index < len(linked_sources):
            src = linked_sources[source_index]
            # Get S3 path from various possible column names
            source_file = (
                src.get('s3_url') or
                src.get('s3_key') or
                src.get('collected_path') or
                src.get('file_path')
            )
            # Ensure S3 path has s3:// prefix if it's a key
            if source_file and not source_file.startswith('s3://') and not source_file.startswith('http'):
                source_file = f"s3://gta-source-files/{source_file}"
            source_url = src.get('source_url')
        elif not source_file and not source_url:
            raise ValueError(f"No source available for StateAct {state_act_id} (index {source_index})")

        # Priority 1: S3 file
        if source_file and source_file.startswith("s3://"):
            try:
                bucket, key = self._parse_s3_url(source_file)
                content_type = self._get_content_type(key)

                if not fetch_content:
                    return SourceResult(
                        source_type="file",
                        source_url=source_file,
                        content=None,
                        content_type=content_type
                    )

                # Fetch file from S3
                file_bytes = await self._fetch_s3_file(bucket, key)

                # Save to persistent storage
                self.storage.save_source(
                    state_act_id=state_act_id,
                    content=file_bytes,
                    content_type=content_type,
                    source_url=source_file
                )

                # Extract text based on type
                if content_type == "pdf":
                    content = self._extract_pdf_text(file_bytes)
                elif content_type == "html":
                    content = self._extract_html_text(file_bytes)
                else:
                    content = file_bytes.decode('utf-8', errors='ignore')

                return SourceResult(
                    source_type="file",
                    source_url=source_file,
                    content=content,
                    content_type=content_type
                )

            except (BotoCoreError, ClientError) as e:
                # S3 access failed, fallback to URL
                pass

        # Priority 2: Source URL
        if source_url:
            try:
                content_type = self._get_content_type(source_url)

                if not fetch_content:
                    return SourceResult(
                        source_type="url",
                        source_url=source_url,
                        content=None,
                        content_type=content_type
                    )

                # Fetch URL content
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(source_url, follow_redirects=True)
                    response.raise_for_status()
                    url_bytes = response.content

                # Save to persistent storage
                self.storage.save_source(
                    state_act_id=state_act_id,
                    content=url_bytes,
                    content_type=content_type,
                    source_url=source_url
                )

                # Extract text based on type
                if content_type == "pdf":
                    content = self._extract_pdf_text(url_bytes)
                elif content_type == "html":
                    content = self._extract_html_text(url_bytes)
                else:
                    content = url_bytes.decode('utf-8', errors='ignore')

                return SourceResult(
                    source_type="url",
                    source_url=source_url,
                    content=content,
                    content_type=content_type
                )

            except Exception as e:
                # URL fetch failed
                return SourceResult(
                    source_type="url",
                    source_url=source_url,
                    content=f"[URL fetch error: {e}]",
                    content_type=content_type
                )

        # No source available
        raise ValueError(f"No source available for StateAct {state_act_id}")
