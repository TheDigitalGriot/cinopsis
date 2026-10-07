"""cc5-batch2 leak 2 (drift 235) - compare_videos metadata + thumbnail yt-dlp calls are gated. Offline.

Uses the REAL ratelimit gate pointed at a temp state file (the test_door2_transcript pattern), so
the door, the cooldown and the record_outcome bookkeeping are exercised rather than stubbed;
subprocess.run is mocked, so no test can reach yt-dlp or the network.
"""
import json
import subprocess
import sys
from types import SimpleNamespace

import pytest

import compare_videos as cv
import ratelimit as rl


@pytest.fixture
def gate(tmp_path, monkeypatch):
    monkeypatch.setattr(rl, "STATE_FILE", tmp_path / "gate" / "fetch_ratelimit.json")
    monkeypatch.setattr(rl, "MIN_SPACING_S", 0.0)
    return rl


@pytest.fixture
def runs(monkeypatch):
    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd)
        if "--dump-json" in cmd:
            return SimpleNamespace(returncode=0, stderr="", stdout=json.dumps(
                {"title": "Real Title", "channel": "Chan", "duration_string": "1:00",
                 "chapters": [{"title": "Intro", "start_time": 0, "end_time": 60}]}))
        return SimpleNamespace(returncode=0, stderr=b"", stdout=b"")
    monkeypatch.setattr(cv.subprocess, "run", fake_run)
    monkeypatch.setattr(cv, "find_ytdlp", lambda: "yt-dlp")
    return calls


def test_metadata_door_is_named_in_ratelimit():
    assert rl.DOOR_METADATA == cv.METADATA_DOOR == "metadata"


def test_metadata_call_passes_the_metadata_door_and_records_outcome(gate, runs, monkeypatch):
    seen = []
    real_check, real_record = gate.check_gate, gate.record_outcome
    monkeypatch.setattr(gate, "check_gate", lambda s="fetch", door=None: seen.append(("gate", s, door)) or real_check(s, door=door))
    monkeypatch.setattr(gate, "record_outcome", lambda ok, d="", door=None: seen.append(("out", ok, door)) or real_record(ok, d, door=door))
    meta = cv.fetch_video_metadata("abc12345678")
    assert meta["title"] == "Real Title" and meta["chapters"][0]["title"] == "Intro"
    assert seen == [("gate", "metadata", "metadata"), ("out", True, "metadata")]
    assert len(runs) == 1


def test_closed_metadata_door_skips_network_and_says_so(gate, runs, capsys):
    gate.record_outcome(False, "HTTP Error 429: Too Many Requests", door="metadata")
    meta = cv.fetch_video_metadata("abc12345678")
    assert runs == []                                            # yt-dlp never spawned
    assert meta["title"] == "Unknown" and meta["chapters"] == []  # the documented failure shape
    assert set(meta) == {"id", "title", "channel", "url", "duration", "upload_date", "view_count", "chapters"}
    out = capsys.readouterr().out
    assert "metadata door closed" in out and "rate-limited" in out   # logged, never silent


def test_closed_metadata_door_skips_thumbnail(gate, runs, capsys):
    gate.record_outcome(False, "HTTP Error 429", door="metadata")
    assert cv.fetch_thumbnail_base64("abc12345678") is None
    assert runs == []
    assert "thumbnail for abc12345678 skipped" in capsys.readouterr().out


def test_thumbnail_call_is_gated_on_the_metadata_door(gate, runs, monkeypatch):
    doors = []
    real = gate.check_gate
    monkeypatch.setattr(gate, "check_gate", lambda s="fetch", door=None: doors.append(door) or real(s, door=door))
    cv.fetch_thumbnail_base64("abc12345678")
    assert doors == ["metadata"] and len(runs) == 1


def test_a_metadata_block_cools_only_the_metadata_door(gate, monkeypatch, capsys):
    monkeypatch.setattr(cv, "find_ytdlp", lambda: "yt-dlp")
    monkeypatch.setattr(cv.subprocess, "run", lambda cmd, **kw: SimpleNamespace(
        returncode=1, stdout="", stderr="ERROR: [youtube] x: HTTP Error 429: Too Many Requests"))
    meta = cv.fetch_video_metadata("abc12345678")
    assert meta["title"] == "Unknown"
    assert "HTTP Error 429" in capsys.readouterr().out
    st = gate.status()
    assert st["doors"]["metadata"]["seconds_left"] > 0
    assert not st["blocked"]                                      # shared cooldown untouched
    gate.check_gate("description", door="timedtext")              # caption door still open
    with pytest.raises(gate.RateLimited):
        gate.check_gate("metadata", door="metadata")


def test_compare_videos_main_caps_new_ids_per_call(monkeypatch, capsys):
    processed = []
    monkeypatch.setattr(cv, "process_video", lambda vid, **kw: processed.append(vid) or {"id": vid})
    monkeypatch.setattr(cv, "add_videos_to_session", lambda sid, videos: "out.json")
    ids = [f"id{i:09d}" for i in range(7)]
    monkeypatch.setattr(sys, "argv", ["compare_videos.py", "--urls", *ids, "--add-to", "s1", "--from-cache"])
    cv.main()
    assert processed == ids[:5]
    assert "clamped to 5" in capsys.readouterr().out
