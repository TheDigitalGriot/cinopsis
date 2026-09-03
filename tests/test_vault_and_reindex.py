"""Tests for the cookie-path resolver, session reindexer, and the flat vault surface.

Everything here is offline: no YouTube, no yt-dlp, no sockets. The server is
exercised through Flask's test_client against a temporary data dir.
"""
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import _utils  # noqa: E402
import reindex_sessions  # noqa: E402
from compare_server import create_app  # noqa: E402


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def write_session(sessions_dir, dir_name, session_id, videos, indexed=True, analysis=None):
    """Create a session dir, optionally adding it to index.json."""
    sdir = sessions_dir / dir_name
    sdir.mkdir(parents=True, exist_ok=True)
    data = {
        "session": {"id": session_id, "title": f"Title {dir_name}",
                    "created_at": "2026-01-01T00:00:00", "video_count": len(videos)},
        "videos": videos,
        "analysis": analysis or {"unified_summary": "", "topics": [],
                                 "disagreements": [], "key_moments": []},
        "stats": {},
    }
    (sdir / "comparison_data.json").write_text(json.dumps(data), encoding="utf-8")

    index_file = sessions_dir / "index.json"
    index = json.loads(index_file.read_text(encoding="utf-8")) if index_file.exists() else []
    if indexed:
        index.append({"id": session_id, "title": f"Title {dir_name}",
                      "created_at": "2026-01-01T00:00:00",
                      "video_count": len(videos), "dir_name": dir_name})
    index_file.write_text(json.dumps(index), encoding="utf-8")
    return sdir


def video(vid, title="T", **extra):
    v = {"id": vid, "title": title, "channel": "Ch", "url": "", "summary": "s",
         "digest": {"core_takeaway": "ct", "key_points": ["a"], "why_it_matters": "w"}}
    v.update(extra)
    return v


# ---------------------------------------------------------------------------
# cookie path resolution (_utils)
# ---------------------------------------------------------------------------
def test_resolve_cookies_prefers_explicit_path(monkeypatch):
    monkeypatch.delenv("CINOPSIS_COOKIES", raising=False)
    assert _utils.resolve_cookies("X:/jar.txt") == "X:/jar.txt"


def test_resolve_cookies_env_wins_over_files_and_skips_existence_check(monkeypatch):
    """An explicitly named jar is returned even if absent, so yt-dlp fails loudly."""
    monkeypatch.setenv("CINOPSIS_COOKIES", "X:/nope.txt")
    assert _utils.resolve_cookies() == "X:/nope.txt"


def test_resolve_cookies_falls_back_to_canonical_dir(monkeypatch, tmp_path):
    """A bare dev run must still find a jar the exporter wrote to the plugin dir."""
    work, canon = tmp_path / "work", tmp_path / "canon"
    work.mkdir()
    canon.mkdir()
    monkeypatch.delenv("CINOPSIS_COOKIES", raising=False)
    monkeypatch.setattr(_utils, "DATA_DIR", work)
    monkeypatch.setenv("CINOPSIS_DATA_DIR", str(canon))
    assert _utils.resolve_cookies() is None          # neither dir has a jar
    (canon / "cookies.txt").write_text("# jar", encoding="utf-8")
    assert _utils.resolve_cookies() == str(canon / "cookies.txt")


def test_resolve_cookies_prefers_data_dir_over_canonical(monkeypatch, tmp_path):
    work, canon = tmp_path / "work", tmp_path / "canon"
    work.mkdir()
    canon.mkdir()
    monkeypatch.delenv("CINOPSIS_COOKIES", raising=False)
    monkeypatch.setattr(_utils, "DATA_DIR", work)
    monkeypatch.setenv("CINOPSIS_DATA_DIR", str(canon))
    (work / "cookies.txt").write_text("# w", encoding="utf-8")
    (canon / "cookies.txt").write_text("# c", encoding="utf-8")
    assert _utils.resolve_cookies() == str(work / "cookies.txt")


def test_cookie_targets_dedupes_when_dirs_collapse(monkeypatch, tmp_path):
    """Under the plugin, DATA_DIR == canonical -> one target, not two writes."""
    monkeypatch.delenv("CINOPSIS_COOKIES", raising=False)
    monkeypatch.setattr(_utils, "DATA_DIR", tmp_path)
    monkeypatch.setenv("CINOPSIS_DATA_DIR", str(tmp_path))
    assert _utils.cookie_targets() == [tmp_path / "cookies.txt"]


def test_cookie_targets_includes_env_first(monkeypatch, tmp_path):
    monkeypatch.setenv("CINOPSIS_COOKIES", str(tmp_path / "env.txt"))
    monkeypatch.setattr(_utils, "DATA_DIR", tmp_path / "d")
    monkeypatch.setenv("CINOPSIS_DATA_DIR", str(tmp_path / "c"))
    targets = _utils.cookie_targets()
    assert targets[0] == tmp_path / "env.txt"
    assert len(targets) == 3


# ---------------------------------------------------------------------------
# reindex_sessions
# ---------------------------------------------------------------------------
def test_reindex_recovers_orphan_and_is_idempotent(tmp_path, capsys):
    sessions = tmp_path / "sessions"
    write_session(sessions, "d-indexed", "aaa", [video("v1")], indexed=True)
    write_session(sessions, "d-orphan", "bbb", [video("v2")], indexed=False)

    added = reindex_sessions.reindex(tmp_path)
    assert [e["dir_name"] for e in added] == ["d-orphan"]

    index = json.loads((sessions / "index.json").read_text(encoding="utf-8"))
    assert {e["dir_name"] for e in index} == {"d-indexed", "d-orphan"}
    # entry shape must match what compare_videos.save_session writes
    assert set(index[0]) == {"id", "title", "created_at", "video_count", "dir_name"}

    # second run changes nothing
    assert reindex_sessions.reindex(tmp_path) == []
    assert len(json.loads((sessions / "index.json").read_text(encoding="utf-8"))) == 2


def test_reindex_skips_dir_whose_id_is_already_indexed(tmp_path):
    """A copied dir sharing an id must not produce a duplicate viewer entry."""
    sessions = tmp_path / "sessions"
    write_session(sessions, "d-one", "same-id", [video("v1")], indexed=True)
    write_session(sessions, "d-copy", "same-id", [video("v1")], indexed=False)
    assert reindex_sessions.reindex(tmp_path) == []


def test_reindex_dry_run_writes_nothing(tmp_path):
    sessions = tmp_path / "sessions"
    write_session(sessions, "d-orphan", "bbb", [video("v2")], indexed=False)
    before = (sessions / "index.json").read_text(encoding="utf-8")
    assert len(reindex_sessions.reindex(tmp_path, dry_run=True)) == 1
    assert (sessions / "index.json").read_text(encoding="utf-8") == before


def test_reindex_survives_a_corrupt_session(tmp_path):
    sessions = tmp_path / "sessions"
    bad = sessions / "d-bad"
    bad.mkdir(parents=True)
    (bad / "comparison_data.json").write_text("{not json", encoding="utf-8")
    write_session(sessions, "d-good", "ccc", [video("v3")], indexed=False)
    added = reindex_sessions.reindex(tmp_path)
    assert [e["dir_name"] for e in added] == ["d-good"]


def test_reindex_reports_stale_entries_without_deleting(tmp_path):
    sessions = tmp_path / "sessions"
    sessions.mkdir(parents=True)
    (sessions / "index.json").write_text(json.dumps(
        [{"id": "x", "title": "gone", "created_at": "", "video_count": 0,
          "dir_name": "missing"}]), encoding="utf-8")
    assert [e["dir_name"] for e in reindex_sessions.find_stale(sessions)] == ["missing"]
    reindex_sessions.reindex(tmp_path)
    index = json.loads((sessions / "index.json").read_text(encoding="utf-8"))
    assert len(index) == 1  # left in place, not silently dropped


def test_reindex_handles_missing_sessions_dir(tmp_path):
    assert reindex_sessions.reindex(tmp_path / "nothing-here") == []


# ---------------------------------------------------------------------------
# the vault surface
# ---------------------------------------------------------------------------
@pytest.fixture
def vault_client(tmp_path):
    sessions = tmp_path / "sessions"
    write_session(sessions, "d-a", "s1", [
        video("v1", "Alpha", channel="ChA"),
        video("v2", "Beta", channel="ChB", harvest=["r1", "r2"]),
    ])
    write_session(sessions, "d-b", "s2", [
        video("v2", "Beta duplicate", channel="ChB"),   # dedup: first wins
        video("unresolved-abc12345", "Gamma", id_status="unresolved",
              title_status="derived-from-digest"),
    ])
    return create_app(data_dir=tmp_path).test_client()


def test_api_vault_dedupes_by_video_id(vault_client):
    rows = vault_client.get("/api/vault").get_json()
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)) == 3
    assert next(r for r in rows if r["id"] == "v2")["title"] == "Beta"


def test_api_vault_exposes_provenance_and_digest_flags(vault_client):
    rows = {r["id"]: r for r in vault_client.get("/api/vault").get_json()}
    assert rows["unresolved-abc12345"]["id_status"] == "unresolved"
    assert rows["unresolved-abc12345"]["title_status"] == "derived-from-digest"
    assert rows["v1"]["id_status"] == "ok"          # defaulted for normal ingests
    assert rows["v2"]["harvest_count"] == 2
    assert rows["v1"]["has_digest"] is True
    assert rows["v1"]["session_title"] == "Title d-a"


def test_api_videos_shape_unchanged(vault_client):
    """The library modal and compose panel depend on this exact payload."""
    rows = vault_client.get("/api/videos").get_json()
    assert set(rows[0]) == {"id", "title", "channel", "duration", "upload_date",
                            "thumbnail_base64", "session_id", "session_title"}


def test_vault_page_served_and_framed(vault_client):
    r = vault_client.get("/vault")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert "griot-flask-frame" in html      # griotwave frame applied
    assert 'id="vault-list"' in html


def test_vault_empty_data_dir_returns_empty_list(tmp_path):
    client = create_app(data_dir=tmp_path).test_client()
    assert client.get("/api/vault").get_json() == []
