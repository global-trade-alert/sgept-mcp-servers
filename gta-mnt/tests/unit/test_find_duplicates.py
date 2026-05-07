"""Tests for the duplicate-detection helpers in api.py.

These cover the pure functions only — the SQL-backed `find_duplicates`
method is exercised end-to-end via the regression script that scans the
JCC-747 trial batch.
"""

import pytest

from gta_mnt.api import extract_decree_numbers, normalize_url


class TestExtractDecreeNumbers:
    def test_brazil_mp(self):
        # Source: SA 96891/96892 leaked-duplicate case (vs SA 96794)
        title = "Brazil: Government zeroes federal taxes on diesel fuel via MP 1340"
        assert "MP 1340" in extract_decree_numbers(title)

    def test_pakistan_vr(self):
        title = "Pakistan: Customs valuation on vacuum flasks (VR 2037/2026)"
        assert "VR 2037/2026" in extract_decree_numbers(title)

    def test_austria_bgbl(self):
        title = "Austria: ÖBAG mandate per BGBl I Nr. 96/2018"
        tokens = extract_decree_numbers(title)
        assert any("BGBl" in t and "96/2018" in t for t in tokens)

    def test_argentina_decreto(self):
        title = "Argentina: Decreto 183/2025 fiscal credit for propane gas"
        assert "Decreto 183/2025" in extract_decree_numbers(title)

    def test_no_decree_returns_empty(self):
        title = "Solidium increases equity stake in Konecranes"
        assert extract_decree_numbers(title) == []

    def test_empty_title(self):
        assert extract_decree_numbers("") == []
        assert extract_decree_numbers(None) == []

    def test_dedupe_case_insensitive(self):
        title = "Decree 100/2026 amends Decree 100/2026"
        tokens = extract_decree_numbers(title)
        # Both occurrences are the same token; we want one entry
        assert len([t for t in tokens if "100/2026" in t]) == 1


class TestNormalizeUrl:
    def test_strips_scheme(self):
        assert normalize_url("https://example.gov/path") == "example.gov/path"
        assert normalize_url("http://example.gov/path") == "example.gov/path"

    def test_strips_www(self):
        assert normalize_url("https://www.example.gov/path") == "example.gov/path"

    def test_strips_trailing_slash(self):
        assert normalize_url("https://example.gov/path/") == "example.gov/path"
        # Root slash preserved
        assert normalize_url("https://example.gov/") == "example.gov/"

    def test_strips_query_and_fragment(self):
        assert normalize_url("https://example.gov/path?utm=foo#section") == "example.gov/path"

    def test_lowercases_host_only(self):
        # Host is case-insensitive; path is case-sensitive on most servers
        assert normalize_url("https://Example.GOV/CamelCasePath") == "example.gov/CamelCasePath"

    def test_empty(self):
        assert normalize_url("") == ""
        assert normalize_url(None) == ""

    def test_two_urls_same_resource_match(self):
        # The whole point of this function — variants resolve identically
        a = "https://www.example.gov/path/?utm_source=twitter"
        b = "http://example.gov/path"
        assert normalize_url(a) == normalize_url(b)
