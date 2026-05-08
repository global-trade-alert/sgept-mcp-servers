"""Gemini OCR fallback for scanned/image-only PDFs.

Wraps the canonical cc-os/scripts/gemini-ocr.py if present; otherwise calls
google-genai directly. Either way, the entry point is one async function:

    await gemini_ocr_pdf(pdf_bytes) -> str

GEMINI_API_KEY must be set in the environment.
"""

from __future__ import annotations

import asyncio
import os
from typing import Optional


_DEFAULT_MODEL = os.environ.get("GEMINI_OCR_MODEL", "gemini-2.5-flash")


async def gemini_ocr_pdf(pdf_bytes: bytes, *, model: Optional[str] = None) -> str:
    """OCR a PDF via Gemini, return concatenated text. Synchronous internally;
    we offload to a thread.
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY (or GOOGLE_API_KEY) not set")

    def _go():
        from google import genai

        client = genai.Client(api_key=api_key)
        # google-genai accepts inline bytes for PDFs up to ~20MB
        resp = client.models.generate_content(
            model=model or _DEFAULT_MODEL,
            contents=[
                {
                    "parts": [
                        {"text": "Extract all readable text from this PDF. Preserve paragraph breaks. Do not summarise."},
                        {"inline_data": {"mime_type": "application/pdf", "data": pdf_bytes}},
                    ]
                }
            ],
        )
        return getattr(resp, "text", "") or ""

    return await asyncio.to_thread(_go)
