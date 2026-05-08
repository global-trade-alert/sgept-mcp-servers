"""URL allowlist + SSRF defence.

Rejects:
- Non-http(s) schemes (file://, ftp://, gopher://, ...)
- Localhost / loopback (127.0.0.0/8, ::1)
- RFC1918 private space (10/8, 172.16/12, 192.168/16)
- Link-local (169.254/16, fe80::/10)
- Cloud metadata endpoints (169.254.169.254, metadata.google.internal, ...)

Allows:
- Public http(s) URLs

The allowlist regex (gov-only, news-only, etc.) is configurable via
SCRAPLING_ALLOW_DOMAINS env var. Default: allow all public addresses.
This is an opt-in tightening for production deployments where you want
to limit which domains the scraper can touch.
"""

from __future__ import annotations

import ipaddress
import os
import re
import socket
from urllib.parse import urlparse


_BLOCKED_HOSTS = {
    "metadata.google.internal",
    "metadata",
    "instance-data",
    "instance-data.ec2.internal",
}


class URLRejected(Exception):
    """Raised when a URL fails the allowlist / SSRF check."""


def _resolve_to_ip(host: str) -> ipaddress._BaseAddress | None:
    """Resolve a hostname to its first IP. Returns None on failure.

    Used so that we reject dns names that resolve to private space, not just
    literal IPs. Best-effort — DNS rebinding can defeat this; defence in depth
    relies on browser sandbox + ulimit.
    """
    try:
        info = socket.getaddrinfo(host, None)
        if not info:
            return None
        sockaddr = info[0][4][0]
        return ipaddress.ip_address(sockaddr)
    except (socket.gaierror, ValueError, IndexError):
        return None


def _is_private_ip(ip: ipaddress._BaseAddress) -> bool:
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def check_url(url: str) -> None:
    """Raise URLRejected if `url` should not be fetched.

    Pass: returns None.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise URLRejected(f"Scheme not allowed: {parsed.scheme!r}")
    if not parsed.hostname:
        raise URLRejected("URL missing hostname")

    host = parsed.hostname.lower()
    if host in _BLOCKED_HOSTS:
        raise URLRejected(f"Blocked host: {host}")

    # Literal IP fast-path
    try:
        ip = ipaddress.ip_address(host)
        if _is_private_ip(ip):
            raise URLRejected(f"Blocked private/loopback IP: {host}")
        return
    except ValueError:
        pass  # not a literal IP, fall through to DNS

    # DNS-resolved IP check (best-effort)
    ip = _resolve_to_ip(host)
    if ip is not None and _is_private_ip(ip):
        raise URLRejected(f"Host {host} resolves to private IP {ip}")

    # Optional domain allowlist (opt-in)
    allow_domains = os.environ.get("SCRAPLING_ALLOW_DOMAINS", "").strip()
    if allow_domains:
        patterns = [p.strip() for p in allow_domains.split(",") if p.strip()]
        if not any(_match_domain(host, p) for p in patterns):
            raise URLRejected(
                f"Host {host} not in SCRAPLING_ALLOW_DOMAINS allowlist"
            )


def _match_domain(host: str, pattern: str) -> bool:
    """Match a host against a pattern.

    Patterns:
    - "example.com" — exact match or subdomain
    - "*.gov.uk" — any subdomain of gov.uk
    - regex:^.*\\.gov$ — explicit regex
    """
    if pattern.startswith("regex:"):
        return bool(re.match(pattern[6:], host))
    if pattern.startswith("*."):
        suffix = pattern[2:]
        return host == suffix or host.endswith("." + suffix)
    return host == pattern or host.endswith("." + pattern)
