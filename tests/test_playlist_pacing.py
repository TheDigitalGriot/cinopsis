"""Network-free tests for the playlist pacing cap (fetch_playlist.py).

Proves the fix for the hammer: the playlist path now surfaces at most N net-new
per run (like the channel path's --playlist-end 10), so a big backlog drains a
bounded batch at a time and can never dump all-N into the fetch pipeline.
fetch_playlist_entries is monkeypatched -- NO network is touched.
"""
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import fetch_playlist as fp  # noqa: E402


@pytest.fixture
def paced(tmp_path, monkeypatch):
    monkeypatch.setattr(fp, "SEEN_FILE", tmp_path / "playlist_seen.json")
    monkeypatch.setattr(fp, "seed_from_catalog", lambda: set())
    monkeypatch.setattr(fp, "resolve_cookies", lambda cookies=None: None)
    return fp


def _entries(n, start=0):
    return [{"id": f"vid{i}", "title": f"t{i}", "url": f"u{i}"} for i in range(start, start + n)]


def test_backlog_drains_bounded(paced, monkeypatch):
    monkeypatch.setattr(paced, "fetch_playlist_entries", lambda *a, **k: _entries(100))
    r1 = paced.fetch_playlist_new(ref="PLtest", max_new=12)
    assert len(r1["new_ids"]) == 12
    assert r1["backlog_new"] == 100
    assert r1["remaining"] == 88
    # a second run surfaces the NEXT 12, never the same ones
    r2 = paced.fetch_playlist_new(ref="PLtest", max_new=12)
    assert len(r2["new_ids"]) == 12
    assert set(r2["new_ids"]).isdisjoint(set(r1["new_ids"]))
    assert r2["remaining"] == 76


def test_steady_state_unchanged(paced, monkeypatch):
    monkeypatch.setattr(paced, "fetch_playlist_entries", lambda *a, **k: _entries(5))
    r = paced.fetch_playlist_new(ref="PLtest", max_new=12)
    assert len(r["new_ids"]) == 5
    assert r["remaining"] == 0


def test_all_bypasses_cap(paced, monkeypatch):
    monkeypatch.setattr(paced, "fetch_playlist_entries", lambda *a, **k: _entries(100))
    r = paced.fetch_playlist_new(ref="PLtest", force_all=True, max_new=12)
    assert len(r["new_ids"]) == 100
    assert r["remaining"] == 0


def test_default_cap_applies_without_arg(paced, monkeypatch):
    monkeypatch.setattr(paced, "fetch_playlist_entries", lambda *a, **k: _entries(100))
    r = paced.fetch_playlist_new(ref="PLtest")  # no max_new -> DEFAULT_MAX_NEW
    assert len(r["new_ids"]) == paced.DEFAULT_MAX_NEW
