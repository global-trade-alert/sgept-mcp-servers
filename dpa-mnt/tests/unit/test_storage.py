"""Unit tests for dpa_mnt ReviewStorage (intervention-scoped, event-prefixed)."""

import pytest

from dpa_mnt.storage import ReviewStorage


@pytest.fixture
def temp_storage(tmp_path):
    return ReviewStorage(base_path=str(tmp_path))


@pytest.fixture
def sample_pdf_bytes():
    return b"%PDF-1.4\nSample PDF content"


@pytest.fixture
def sample_html_bytes():
    return b"<html><body><h1>DPA Event</h1></body></html>"


# ============================================================================
# Path management
# ============================================================================


def test_get_review_path_creates_intervention_folder(temp_storage):
    path = temp_storage.get_review_path(intervention_id=777)
    assert path.exists()
    assert path.is_dir()
    assert path.name == "777"


def test_get_review_path_idempotent(temp_storage):
    p1 = temp_storage.get_review_path(intervention_id=777)
    p2 = temp_storage.get_review_path(intervention_id=777)
    assert p1 == p2


def test_event_prefix_format(temp_storage):
    assert temp_storage._evt_prefix(501) == "evt-501"


# ============================================================================
# Source saving (intervention-scoped, event-prefixed)
# ============================================================================


def test_save_pdf_source_writes_event_prefixed_file(temp_storage, sample_pdf_bytes):
    path = temp_storage.save_source(
        intervention_id=777,
        event_id=501,
        content=sample_pdf_bytes,
        content_type="pdf",
        source_url="https://example.com/policy.pdf",
    )
    assert path.exists()
    assert path.name == "evt-501-source.pdf"
    assert path.parent.name == "777"
    assert path.read_bytes() == sample_pdf_bytes

    url_path = path.parent / "evt-501-source-url.txt"
    assert url_path.exists()
    assert url_path.read_text() == "https://example.com/policy.pdf"


def test_save_html_source(temp_storage, sample_html_bytes):
    path = temp_storage.save_source(
        intervention_id=777,
        event_id=501,
        content=sample_html_bytes,
        content_type="html",
        source_url="https://example.com/policy",
    )
    assert path.name == "evt-501-source.html"
    assert path.read_bytes() == sample_html_bytes


def test_save_text_source(temp_storage):
    path = temp_storage.save_source(
        intervention_id=777,
        event_id=501,
        content=b"Plain text policy",
        content_type="text",
        source_url="https://example.com/policy.txt",
    )
    assert path.name == "evt-501-source.txt"


def test_save_source_scopes_per_event(temp_storage, sample_pdf_bytes):
    """Two events on the same intervention land in the same folder under
    different evt- prefixes. This is the whole point of the DPA storage layout."""
    p1 = temp_storage.save_source(
        intervention_id=777,
        event_id=501,
        content=sample_pdf_bytes,
        content_type="pdf",
        source_url="https://a",
    )
    p2 = temp_storage.save_source(
        intervention_id=777,
        event_id=502,
        content=sample_pdf_bytes,
        content_type="pdf",
        source_url="https://b",
    )
    assert p1.parent == p2.parent
    assert p1.name != p2.name
    assert p1.name == "evt-501-source.pdf"
    assert p2.name == "evt-502-source.pdf"


# ============================================================================
# Comment saving
# ============================================================================


def test_save_first_comment_creates_file_with_header(temp_storage):
    path = temp_storage.save_comment(
        intervention_id=777,
        event_id=501,
        comment_text="Initial review comment.",
        comment_id=100,
    )
    assert path.name == "evt-501-comments.md"
    content = path.read_text()
    assert "# Review Comments - Event 501" in content
    assert "Buzessa Claudini automated review system" in content
    assert "## Comment #100" in content
    assert "Initial review comment." in content


def test_save_multiple_comments_append(temp_storage):
    temp_storage.save_comment(intervention_id=777, event_id=501, comment_text="First", comment_id=1)
    path = temp_storage.save_comment(intervention_id=777, event_id=501, comment_text="Second", comment_id=2)
    content = path.read_text()
    assert "## Comment #1" in content
    assert "First" in content
    assert "## Comment #2" in content
    assert "Second" in content


def test_save_comment_without_id(temp_storage):
    path = temp_storage.save_comment(
        intervention_id=777,
        event_id=501,
        comment_text="No id",
    )
    content = path.read_text()
    assert "## Comment" in content
    assert "No id" in content


# ============================================================================
# Review log
# ============================================================================


def test_save_review_log_approve(temp_storage):
    path = temp_storage.save_log(
        intervention_id=777,
        event_id=501,
        source_url="https://example.com/policy.pdf",
        fields_validated=["event_title", "event_date", "event_type"],
        issues_found=[],
        decision="APPROVE",
        actions_taken=["BC review issue tagged"],
    )
    assert path.name == "evt-501-review-log.md"
    content = path.read_text()
    assert "# Review Log - Event 501" in content
    assert "**Decision:** APPROVE" in content
    assert "No issues found" in content
    assert "BC review issue tagged" in content


def test_save_review_log_disapprove(temp_storage):
    path = temp_storage.save_log(
        intervention_id=777,
        event_id=501,
        source_url="https://example.com/policy.pdf",
        fields_validated=["event_title", "event_date"],
        issues_found=["Date mismatch: source says 2026-01-20, entry says 2026-01-15"],
        decision="DISAPPROVE",
        actions_taken=[
            "Issue comment posted",
            "Status changed to Under revision (status_id=5)",
        ],
    )
    content = path.read_text()
    assert "**Decision:** DISAPPROVE" in content
    assert "Date mismatch" in content
    assert "Status changed to Under revision" in content


def test_save_review_log_overwrites(temp_storage):
    # First log
    temp_storage.save_log(
        intervention_id=777,
        event_id=501,
        source_url="https://a",
        fields_validated=["event_title"],
        issues_found=[],
        decision="APPROVE",
        actions_taken=[],
    )
    # Second log overwrites.
    path = temp_storage.save_log(
        intervention_id=777,
        event_id=501,
        source_url="https://b",
        fields_validated=["event_title", "event_date"],
        issues_found=["mismatch"],
        decision="DISAPPROVE",
        actions_taken=["comment posted"],
    )
    content = path.read_text()
    assert "**Decision:** DISAPPROVE" in content
    assert "https://b" in content
    assert "https://a" not in content


# ============================================================================
# Helpers
# ============================================================================


def test_get_source_path_pdf(temp_storage, sample_pdf_bytes):
    temp_storage.save_source(
        intervention_id=777,
        event_id=501,
        content=sample_pdf_bytes,
        content_type="pdf",
        source_url="https://example.com/policy.pdf",
    )
    path = temp_storage.get_source_path(intervention_id=777, event_id=501)
    assert path is not None
    assert path.name == "evt-501-source.pdf"


def test_get_source_path_none_when_missing(temp_storage):
    temp_storage.get_review_path(intervention_id=777)
    assert temp_storage.get_source_path(intervention_id=777, event_id=501) is None


def test_review_exists_true_after_log(temp_storage):
    temp_storage.save_log(
        intervention_id=777,
        event_id=501,
        source_url="https://a",
        fields_validated=[],
        issues_found=[],
        decision="APPROVE",
        actions_taken=[],
    )
    assert temp_storage.review_exists(intervention_id=777, event_id=501) is True


def test_review_exists_false_when_missing(temp_storage):
    assert temp_storage.review_exists(intervention_id=777, event_id=501) is False
