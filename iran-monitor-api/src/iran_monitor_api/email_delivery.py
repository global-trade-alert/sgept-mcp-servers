"""Email delivery for completed queries.

When a CreateQueryRequest sets `deliver_to`, the worker (after producing the
signed audit record) sends an HTML email to that address with:
  - Subject: "Iran Monitor scenario assessment — {short scenario}"
  - HTML body: the briefing_markdown rendered to HTML
  - JSON attachment: the full result + signed audit
  - Plain-text fallback for clients that don't render HTML

SMTP credentials live in SOPS-encrypted env (same pattern as the existing
metis-cos-inbox / notify-reply.py infrastructure).
"""

from __future__ import annotations

import json
import logging
import re
import smtplib
import ssl
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any
from uuid import UUID

from .config import get_settings

logger = logging.getLogger(__name__)


# Minimal markdown → HTML so we don't pull in a dependency. Covers the
# subset the briefing-writer uses: # / ## / ### headers, paragraphs,
# bullet lists, code spans, blockquotes.
def _markdown_to_html(md: str) -> str:
    lines = md.splitlines()
    html: list[str] = []
    in_list = False
    in_para: list[str] = []

    def flush_para():
        if in_para:
            html.append("<p>" + "<br>".join(_inline(l) for l in in_para) + "</p>")
            in_para.clear()

    def _inline(s: str) -> str:
        # Escape angle brackets first
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # Inline code
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        # Bold
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        # Italics
        s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", s)
        # Links
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
        return s

    for raw in lines:
        line = raw.rstrip()
        if not line:
            flush_para()
            if in_list:
                html.append("</ul>")
                in_list = False
            continue
        if line.startswith("# "):
            flush_para()
            if in_list:
                html.append("</ul>"); in_list = False
            html.append(f"<h2>{_inline(line[2:])}</h2>")
        elif line.startswith("## "):
            flush_para()
            if in_list:
                html.append("</ul>"); in_list = False
            html.append(f"<h3>{_inline(line[3:])}</h3>")
        elif line.startswith("### "):
            flush_para()
            if in_list:
                html.append("</ul>"); in_list = False
            html.append(f"<h4>{_inline(line[4:])}</h4>")
        elif line.startswith("- ") or line.startswith("* "):
            flush_para()
            if not in_list:
                html.append("<ul>"); in_list = True
            html.append(f"<li>{_inline(line[2:])}</li>")
        elif line.startswith("> "):
            flush_para()
            if in_list:
                html.append("</ul>"); in_list = False
            html.append(f'<blockquote>{_inline(line[2:])}</blockquote>')
        elif line.startswith("---"):
            flush_para()
            if in_list:
                html.append("</ul>"); in_list = False
            html.append("<hr>")
        else:
            in_para.append(line)

    flush_para()
    if in_list:
        html.append("</ul>")

    return "\n".join(html)


_EMAIL_CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 720px; margin: 24px auto; padding: 0 16px; color: #1a1a1a; line-height: 1.5; }
h2 { border-bottom: 1px solid #ddd; padding-bottom: 8px; margin-top: 32px; }
h3 { margin-top: 24px; }
h4 { margin-top: 16px; color: #333; }
blockquote { border-left: 3px solid #888; padding-left: 12px; color: #444; margin: 12px 0; }
code { background: #f4f4f4; padding: 2px 5px; border-radius: 3px; font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 0.92em; }
ul { padding-left: 24px; }
hr { border: 0; border-top: 1px solid #ddd; margin: 32px 0; }
.footer { color: #888; font-size: 0.85em; margin-top: 32px; padding-top: 12px; border-top: 1px solid #eee; }
"""


class EmailDeliveryError(Exception):
    pass


def render_html_email(briefing_md: str, query_id: UUID, intelligence_base_hash: str) -> str:
    body_html = _markdown_to_html(briefing_md) if briefing_md else "<p><em>(No briefing content available.)</em></p>"
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>{_EMAIL_CSS}</style></head>
<body>
{body_html}
<div class="footer">
  Query ID: <code>{query_id}</code><br>
  Intelligence base: <code>{intelligence_base_hash}</code><br>
  The attached <code>iran-monitor-result.json</code> contains the full structured response and the Ed25519-signed audit record.
  Verify the signature against the public key at <code>https://api.iran-monitor.sgept.org/.well-known/iran-monitor-signing-key.pub</code>.
</div>
</body></html>"""


def render_text_email(briefing_md: str, query_id: UUID) -> str:
    return (
        (briefing_md or "(No briefing content available.)")
        + f"\n\n--\nQuery ID: {query_id}\n"
        + "Verify the attached audit signature against\n"
        + "https://api.iran-monitor.sgept.org/.well-known/iran-monitor-signing-key.pub\n"
    )


def short_scenario(scenario: str, max_chars: int = 60) -> str:
    s = re.sub(r"\s+", " ", scenario).strip()
    return s if len(s) <= max_chars else s[: max_chars - 1] + "…"


def send_completion_email(
    *,
    deliver_to: str,
    scenario: str,
    query_id: UUID,
    intelligence_base_hash: str,
    briefing_markdown: str,
    full_result_json: dict,
) -> None:
    """Send the completion email. Raises EmailDeliveryError on failure;
    caller decides whether to fail the query or just log."""
    settings = get_settings()

    if not settings.smtp_host or not settings.smtp_from:
        raise EmailDeliveryError(
            "SMTP not configured (IRAN_API_SMTP_HOST / IRAN_API_SMTP_FROM missing)"
        )

    msg = MIMEMultipart("mixed")
    msg["From"] = settings.smtp_from
    msg["To"] = deliver_to
    msg["Subject"] = f"Iran Monitor scenario assessment — {short_scenario(scenario)}"

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(render_text_email(briefing_markdown, query_id), "plain", "utf-8"))
    alt.attach(MIMEText(render_html_email(briefing_markdown, query_id, intelligence_base_hash), "html", "utf-8"))
    msg.attach(alt)

    att = MIMEApplication(json.dumps(full_result_json, indent=2).encode("utf-8"), _subtype="json")
    att.add_header(
        "Content-Disposition", "attachment", filename=f"iran-monitor-result-{query_id}.json"
    )
    msg.attach(att)

    try:
        if settings.smtp_use_ssl:
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, context=ctx) as s:
                if settings.smtp_username:
                    s.login(settings.smtp_username, settings.smtp_password)
                s.send_message(msg)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as s:
                s.ehlo()
                if settings.smtp_use_starttls:
                    s.starttls(context=ssl.create_default_context())
                    s.ehlo()
                if settings.smtp_username:
                    s.login(settings.smtp_username, settings.smtp_password)
                s.send_message(msg)
        logger.info("delivered query %s to %s", query_id, deliver_to)
    except Exception as e:
        raise EmailDeliveryError(f"SMTP send failed: {e}") from e
