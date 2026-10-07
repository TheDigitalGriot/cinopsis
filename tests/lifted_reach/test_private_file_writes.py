# Lifted test (partial) - Agent-Reach at the pinned sha, exercising scripts/reach.
# Upstream test code is verbatim between the LIFT fences; changed lines end in '# seam:'.
# Not lifted (they exercise parked upstream modules, see scripts/lift_parked.json):
#   test_private_file_writes.py:13-13 import of parked module
#   test_private_file_writes.py:14-14 import of parked module
#   test_private_file_writes.py:47-60 test_legacy_xfetch_sync_refuses_target_symlink uses _sync_xfetch_session
#   test_private_file_writes.py:63-77 test_legacy_xfetch_sync_refuses_parent_symlink uses _sync_xfetch_session
#   test_private_file_writes.py:80-92 test_legacy_xfetch_sync_refuses_ancestor_symlink uses _sync_xfetch_session
#   test_private_file_writes.py:95-124 test_credential_writes_honor_home_when_expanduser_disagrees uses _sync_xfetch_session
#   test_private_file_writes.py:127-148 test_expanduser_fallback_still_refuses_symlinked_profile uses _sync_xfetch_session
#   test_private_file_writes.py:151-161 test_legacy_xfetch_sync_refuses_oversized_existing_session uses _sync_xfetch_session
#   test_private_file_writes.py:164-177 test_legacy_bird_sync_refuses_target_symlink uses _sync_bird_env
#   test_private_file_writes.py:180-219 test_xhs_cookie_editor_json_ignores_non_xhs_domains uses cli
#   test_private_file_writes.py:222-257 test_xhs_cookie_editor_json_fails_without_valid_xhs_cookie uses cli
#   test_private_file_writes.py:260-279 test_xhs_local_fallback_refuses_target_symlink uses cli
#   test_private_file_writes.py:282-313 test_xhs_docker_success_via_configure_command_does_not_exit uses cli
#   test_private_file_writes.py:316-353 test_xhs_docker_failure_via_configure_command_exits_one uses cli
#   test_private_file_writes.py:356-399 test_ytdlp_config_write_refuses_target_symlink uses cli
#   test_private_file_writes.py:402-432 test_transcribe_cli_scrubs_credentials_from_errors uses cli
#   test_private_file_writes.py:435-478 test_safe_install_with_proxy_makes_no_persistent_writes uses cli
#   test_private_file_writes.py:481-515 test_install_is_safe_by_default uses cli
#   test_private_file_writes.py:518-554 test_install_system_flag_explicitly_enables_writes uses cli
#   test_private_file_writes.py:557-582 test_install_system_exits_nonzero_when_core_steps_fail uses cli
#   test_private_file_writes.py:585-615 test_install_system_exits_nonzero_when_requested_channel_fails uses cli
#   test_private_file_writes.py:618-640 test_install_system_exits_nonzero_when_skill_install_fails uses cli

# >>> LIFT agent-reach@a19a171f tests/test_private_file_writes.py:1-11
"""Security regressions for local credential and tool configuration writes."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from argparse import Namespace

import pytest
# <<< LIFT

# >>> LIFT agent-reach@a19a171f tests/test_private_file_writes.py:15-44
from reach import paths  # seam: package import


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission semantics")
def test_atomic_private_text_write_is_0600(tmp_path):
    target = tmp_path / "private" / "secret.txt"

    paths.atomic_write_private_text(target, "secret")

    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert stat.S_IMODE(target.parent.stat().st_mode) == 0o700


def test_atomic_private_text_write_preserves_old_file_on_replace_failure(
    tmp_path, monkeypatch
):
    target = tmp_path / "private" / "secret.txt"
    target.parent.mkdir()
    target.write_text("keep-old", encoding="utf-8")

    def fail_replace(*_args, **_kwargs):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(paths.os, "replace", fail_replace)

    with pytest.raises(OSError, match="replace failure"):
        paths.atomic_write_private_text(target, "new-secret")

    assert target.read_text(encoding="utf-8") == "keep-old"
    assert list(target.parent.glob(".secret.txt.*.tmp")) == []
# <<< LIFT
