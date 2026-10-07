# Lifted test (partial) - Agent-Reach at the pinned sha, exercising scripts/reach.
# Upstream test code is verbatim between the LIFT fences; changed lines end in '# seam:'.
# Not lifted (they exercise parked upstream modules, see scripts/lift_parked.json):
#   test_url_security.py:5-5 import of parked module
#   test_url_security.py:6-6 import of parked module
#   test_url_security.py:7-7 import of parked module
#   test_url_security.py:8-8 import of parked module
#   test_url_security.py:9-9 import of parked module
#   test_url_security.py:10-10 import of parked module
#   test_url_security.py:11-11 import of parked module
#   test_url_security.py:12-12 import of parked module
#   test_url_security.py:13-13 import of parked module
#   test_url_security.py:14-14 import of parked module
#   test_url_security.py:15-15 import of parked module
#   test_url_security.py:20-33 test_credential_channels_accept_exact_hosts_and_subdomains uses TwitterChannel
#   test_url_security.py:36-53 test_credential_channels_reject_lookalikes_and_userinfo uses TwitterChannel
#   test_url_security.py:56-105 test_fixed_domain_channels_accept_subdomains_and_explicit_ports uses GitHubChannel
#   test_url_security.py:108-126 test_fixed_domain_channels_reject_suffix_lookalikes_and_userinfo uses GitHubChannel

# >>> LIFT agent-reach@a19a171f tests/test_url_security.py:1-3
"""Credential-bearing channels must reject lookalike or disguised hosts."""

import pytest
# <<< LIFT

# >>> LIFT agent-reach@a19a171f tests/test_url_security.py:16-17
from reach.youtube import YouTubeChannel  # seam: package import
from reach.url import host_matches  # seam: package import
# <<< LIFT

# >>> LIFT agent-reach@a19a171f tests/test_url_security.py:129-139
@pytest.mark.parametrize(
    "malicious_url",
    [
        "https://x.com:not-a-port/path",
        "https://x.com:65536/path",
        "https://x.com:-1/path",
        "https://x.com:999999999999/path",
    ],
)
def test_host_matches_rejects_invalid_ports(malicious_url):
    assert not host_matches(malicious_url, "x.com")
# <<< LIFT
