"""SSRF / allowlist tests. No network, no scrapling import."""

import os

import pytest

from scrapling_mnt.allowlist import URLRejected, check_url


@pytest.mark.parametrize("url", [
    "https://www.example.com/",
    "https://example.gov.uk/path",
    "http://example.com/",
])
def test_public_https_passes(url):
    check_url(url)


@pytest.mark.parametrize("url", [
    "file:///etc/passwd",
    "ftp://example.com/file",
    "gopher://example.com/",
    "javascript:alert(1)",
])
def test_non_http_rejected(url):
    with pytest.raises(URLRejected):
        check_url(url)


@pytest.mark.parametrize("url", [
    "http://127.0.0.1/",
    "http://127.0.0.1:8080/admin",
    "http://localhost/",
    "http://10.0.0.1/",
    "http://192.168.1.1/",
    "http://172.16.0.1/",
    "http://169.254.169.254/latest/meta-data/",
])
def test_private_loopback_rejected(url):
    with pytest.raises(URLRejected):
        check_url(url)


def test_metadata_host_rejected():
    with pytest.raises(URLRejected):
        check_url("http://metadata.google.internal/computeMetadata/v1/")


def test_allowlist_opt_in(monkeypatch):
    monkeypatch.setenv("SCRAPLING_ALLOW_DOMAINS", "gov.uk,*.gov.au")
    check_url("https://example.gov.uk/x")
    check_url("https://www.foo.gov.au/y")
    with pytest.raises(URLRejected):
        check_url("https://example.com/")


def test_allowlist_regex(monkeypatch):
    monkeypatch.setenv("SCRAPLING_ALLOW_DOMAINS", r"regex:^.*\.gov$")
    check_url("https://x.gov/")
    with pytest.raises(URLRejected):
        check_url("https://x.com/")
