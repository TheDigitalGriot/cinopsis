# Lifted test (partial) - Agent-Reach at the pinned sha, exercising scripts/reach.
# Upstream test code is verbatim between the LIFT fences; changed lines end in '# seam:'.
# Not lifted (they exercise parked upstream modules, see scripts/lift_parked.json):
#   test_scrub_credentials.py:8-8 import of parked module
#   test_scrub_credentials.py:9-9 import of parked module
#   test_scrub_credentials.py:10-10 import of parked module
#   test_scrub_credentials.py:11-11 import of parked module
#   test_scrub_credentials.py:12-12 import of parked module
#   test_scrub_credentials.py:58-78 test_channel_health_messages_scrub_url_secrets uses v2ex_module
#   test_scrub_credentials.py:81-103 test_browser_backend_errors_scrub_url_secrets uses cookie_extract

# >>> LIFT agent-reach@a19a171f tests/test_scrub_credentials.py:1-6
"""Secrets embedded in URLs must not reach user-facing diagnostics."""

import sys
from types import SimpleNamespace

import pytest
# <<< LIFT

# >>> LIFT agent-reach@a19a171f tests/test_scrub_credentials.py:13-55
from reach.text import scrub_url_credentials  # seam: package import


def test_scrubs_userinfo_and_sensitive_query_values():
    raw = (
        "proxy http://user:pass@proxy.example:8080 failed; "
        "upstream https://api.example.test/path?access_token=secret"
        "&page=2&api_key=another-secret"
    )

    scrubbed = scrub_url_credentials(raw)

    assert "user:pass" not in scrubbed
    assert "secret" not in scrubbed
    assert "another-secret" not in scrubbed
    assert "http://***@proxy.example:8080" in scrubbed
    assert "access_token=***" in scrubbed
    assert "page=2" in scrubbed
    assert "api_key=***" in scrubbed


def test_scrubs_multiple_schemes_and_fragment_tokens():
    raw = (
        "socks5://token@host:1080 "
        "https://example.test/#auth_token=fragment-secret"
    )

    scrubbed = scrub_url_credentials(ValueError(raw))

    assert scrubbed == (
        "socks5://***@host:1080 "
        "https://example.test/#auth_token=***"
    )


def test_scrubs_bare_user_password_host_diagnostics():
    raw = "proxy handshake for user:pass@proxy.test failed"
    assert scrub_url_credentials(raw) == "proxy handshake for ***@proxy.test failed"


def test_leaves_non_secret_urls_and_plain_text_unchanged():
    raw = "See https://example.test/search?q=python&page=2 after timeout"
    assert scrub_url_credentials(raw) == raw
# <<< LIFT
