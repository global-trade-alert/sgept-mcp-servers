"""Email delivery: markdown→HTML rendering, message assembly, SMTP error paths."""

from __future__ import annotations

import smtplib
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from iran_monitor_api.config import get_settings
from iran_monitor_api.email_delivery import (
    EmailDeliveryError,
    _markdown_to_html,
    render_html_email,
    render_text_email,
    send_completion_email,
    short_scenario,
)


def test_markdown_to_html_handles_headers_bullets_blockquotes():
    md = "# H1\n\n## H2\n\n- one\n- two\n\n> a quote\n\nplain paragraph"
    html = _markdown_to_html(md)
    assert "<h2>H1</h2>" in html
    assert "<h3>H2</h3>" in html
    assert "<ul>" in html and "<li>one</li>" in html
    assert "<blockquote>a quote</blockquote>" in html
    assert "<p>plain paragraph</p>" in html


def test_markdown_to_html_escapes_angle_brackets():
    md = "value <unsafe>"
    html = _markdown_to_html(md)
    assert "&lt;unsafe&gt;" in html


def test_markdown_to_html_renders_inline_code_and_links():
    md = "see `the doc` and [here](https://example.com)"
    html = _markdown_to_html(md)
    assert "<code>the doc</code>" in html
    assert '<a href="https://example.com">here</a>' in html


def test_short_scenario_truncates():
    long = "x" * 200
    assert len(short_scenario(long)) <= 60
    assert short_scenario(long).endswith("…")


def test_render_html_email_includes_query_id_and_hash():
    qid = uuid4()
    html = render_html_email("# x", qid, "sha256:abc")
    assert str(qid) in html
    assert "sha256:abc" in html
    assert "iran-monitor-signing-key.pub" in html


def test_render_text_email_has_verify_pointer():
    qid = uuid4()
    text = render_text_email("hi", qid)
    assert "iran-monitor-signing-key.pub" in text
    assert str(qid) in text


def test_send_completion_email_errors_without_smtp_host(isolated_env, monkeypatch):
    monkeypatch.setenv("IRAN_API_SMTP_HOST", "")
    monkeypatch.setenv("IRAN_API_SMTP_FROM", "")
    from iran_monitor_api import config as cfg
    cfg.reset_settings_for_tests()
    with pytest.raises(EmailDeliveryError, match="SMTP not configured"):
        send_completion_email(
            deliver_to="x@example.com",
            scenario="x",
            query_id=uuid4(),
            intelligence_base_hash="sha256:abc",
            briefing_markdown="hi",
            full_result_json={},
        )


def test_send_completion_email_uses_smtp_starttls(isolated_env, monkeypatch):
    monkeypatch.setenv("IRAN_API_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("IRAN_API_SMTP_PORT", "587")
    monkeypatch.setenv("IRAN_API_SMTP_USE_SSL", "false")
    monkeypatch.setenv("IRAN_API_SMTP_USE_STARTTLS", "true")
    monkeypatch.setenv("IRAN_API_SMTP_USERNAME", "user")
    monkeypatch.setenv("IRAN_API_SMTP_PASSWORD", "pass")
    monkeypatch.setenv("IRAN_API_SMTP_FROM", "from@example.com")
    from iran_monitor_api import config as cfg
    cfg.reset_settings_for_tests()

    mock_smtp = MagicMock()
    mock_ctx_mgr = MagicMock()
    mock_ctx_mgr.__enter__.return_value = mock_smtp
    mock_ctx_mgr.__exit__.return_value = False

    with patch("smtplib.SMTP", return_value=mock_ctx_mgr) as smtp_class:
        send_completion_email(
            deliver_to="risk@hedge-fund.com",
            scenario="Iran scenario test",
            query_id=uuid4(),
            intelligence_base_hash="sha256:test",
            briefing_markdown="# Test\n\nbody",
            full_result_json={"a": 1},
        )

    smtp_class.assert_called_once_with("smtp.example.com", 587)
    mock_smtp.starttls.assert_called_once()
    mock_smtp.login.assert_called_once_with("user", "pass")
    mock_smtp.send_message.assert_called_once()
    msg = mock_smtp.send_message.call_args[0][0]
    assert msg["To"] == "risk@hedge-fund.com"
    assert msg["From"] == "from@example.com"
    assert "Iran scenario test" in msg["Subject"]


def test_send_completion_email_wraps_smtp_errors(isolated_env, monkeypatch):
    monkeypatch.setenv("IRAN_API_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("IRAN_API_SMTP_FROM", "from@example.com")
    from iran_monitor_api import config as cfg
    cfg.reset_settings_for_tests()

    mock_smtp = MagicMock()
    mock_smtp.send_message.side_effect = smtplib.SMTPException("connection refused")
    mock_ctx_mgr = MagicMock()
    mock_ctx_mgr.__enter__.return_value = mock_smtp
    mock_ctx_mgr.__exit__.return_value = False

    with patch("smtplib.SMTP", return_value=mock_ctx_mgr):
        with pytest.raises(EmailDeliveryError, match="SMTP send failed"):
            send_completion_email(
                deliver_to="x@example.com",
                scenario="x",
                query_id=uuid4(),
                intelligence_base_hash="sha256:abc",
                briefing_markdown="x",
                full_result_json={},
            )
