# tests/test_capture_frames.py
import json
import subprocess
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from capture_frames import extract_video_id, format_timestamp, build_ffmpeg_cmd


class TestExtractVideoId(unittest.TestCase):
    def test_full_url(self):
        self.assertEqual(extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ"), "dQw4w9WgXcQ")

    def test_short_url(self):
        self.assertEqual(extract_video_id("https://youtu.be/dQw4w9WgXcQ"), "dQw4w9WgXcQ")

    def test_bare_id(self):
        self.assertEqual(extract_video_id("dQw4w9WgXcQ"), "dQw4w9WgXcQ")


class TestFormatTimestamp(unittest.TestCase):
    def test_seconds_only(self):
        self.assertEqual(format_timestamp(45), "00:00:45")

    def test_minutes_and_seconds(self):
        self.assertEqual(format_timestamp(261), "00:04:21")

    def test_hours(self):
        self.assertEqual(format_timestamp(3661), "01:01:01")


class TestBuildFfmpegCmd(unittest.TestCase):
    def test_command_structure(self):
        cmd = build_ffmpeg_cmd("https://example.com/stream", 261, "/tmp/out.png")
        self.assertIn("ffmpeg", cmd[0])
        self.assertIn("-ss", cmd)
        self.assertIn("00:04:21", cmd)
        self.assertEqual(cmd[-1], "/tmp/out.png")


class TestBatchResolvesOnce(unittest.TestCase):
    """Drift 371: one stream-URL resolve per video per batch, not one per frame."""

    VID = "dQw4w9WgXcQ"
    TIMESTAMPS = [10, 20, 30, 40, 50, 60, 70, 80]

    def setUp(self):
        import tempfile
        import capture_frames
        self.cf = capture_frames
        self._tmp = tempfile.TemporaryDirectory()
        self.out = Path(self._tmp.name)
        self.ffmpeg_urls = []
        self.fail_first_ffmpeg = False
        patchers = [
            patch.object(capture_frames, "find_ffmpeg", return_value="ffmpeg"),
            patch.object(capture_frames.subprocess, "run", side_effect=self._fake_run),
        ]
        for p in patchers:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self._tmp.cleanup)

    def _fake_run(self, cmd, **kwargs):
        # Fake ffmpeg: record the URL it was handed, write the PNG unless told to fail
        self.ffmpeg_urls.append(cmd[cmd.index("-i") + 1])
        if self.fail_first_ffmpeg and len(self.ffmpeg_urls) == 1:
            return MagicMock(returncode=1)
        Path(cmd[-1]).write_bytes(b"png")
        return MagicMock(returncode=0)

    def _resolver(self, *urls):
        return patch.object(self.cf, "get_stream_url", side_effect=list(urls))

    def test_a_uncached_resolves_once(self):
        with self._resolver("https://s/1") as resolve:
            results = self.cf.capture_frames_batch(self.VID, self.TIMESTAMPS, self.out)
        self.assertEqual(resolve.call_count, 1)
        self.assertEqual(len(self.ffmpeg_urls), 8)
        self.assertTrue(all(r["base64"] for r in results))

    def test_b_all_cached_resolves_zero(self):
        for ts in self.TIMESTAMPS:
            (self.out / f"{self.VID}_{ts}.png").write_bytes(b"png")
        with self._resolver() as resolve:
            results = self.cf.capture_frames_batch(self.VID, self.TIMESTAMPS, self.out)
        self.assertEqual(resolve.call_count, 0)
        self.assertEqual(self.ffmpeg_urls, [])
        self.assertTrue(all(r["base64"] for r in results))

    def test_c_failed_resolve_not_reasked(self):
        with self._resolver(None, "https://s/never") as resolve:
            results = self.cf.capture_frames_batch(self.VID, self.TIMESTAMPS, self.out)
        self.assertEqual(resolve.call_count, 1)
        self.assertEqual(len(results), 8)
        self.assertTrue(all(r["base64"] is None for r in results))
        self.assertEqual(self.ffmpeg_urls, [])

    def test_d_expired_url_re_resolved_once(self):
        self.fail_first_ffmpeg = True
        with self._resolver("https://s/stale", "https://s/fresh", "https://s/never") as resolve:
            results = self.cf.capture_frames_batch(self.VID, self.TIMESTAMPS, self.out)
        self.assertEqual(resolve.call_count, 2)
        # frame 1 tried on the stale URL, retried once on the fresh one; the rest reuse fresh
        self.assertEqual(self.ffmpeg_urls, ["https://s/stale"] + ["https://s/fresh"] * 8)
        self.assertTrue(all(r["base64"] for r in results))

    def test_e_single_frame_still_resolves_itself(self):
        with self._resolver("https://s/1") as resolve:
            b64 = self.cf.capture_frame(self.VID, 10, self.out)
        self.assertEqual(resolve.call_count, 1)
        self.assertEqual(self.ffmpeg_urls, ["https://s/1"])
        self.assertIsNotNone(b64)


# ---------------------------------------------------------------------------
# drift 371 stage B: the session frames engine defaults to local, chosen by ONE
# resolver (capture_frames.default_engine) shared by the CLI and harvest_frames.
# The engine functions are replaced with recorders: no ffmpeg, no network.
# ---------------------------------------------------------------------------
import json as _json

import pytest

import capture_frames as _cf

_VID = "chooserVid1"


def _chooser_session(tmp_path):
    sdir = tmp_path / "sessions" / "s1"
    sdir.mkdir(parents=True)
    step = {"video_id": _VID, "index": 1, "t_start": 1, "frame_ref": None}
    (sdir / "comparison_data.json").write_text(
        _json.dumps({"analysis": {"workflow_steps": [step], "key_moments": []}}), encoding="utf-8")
    return sdir


@pytest.fixture
def chooser(tmp_path, monkeypatch):
    """No env set, session on disk, both session engines recorded (CLI + MCP bindings)."""
    # Import mcp_server BEFORE patching capture_frames: it binds these names at import time.
    mcp = None
    try:
        import mcp_server as mcp
    except ImportError:
        pass
    monkeypatch.delenv("CINOPSIS_FRAMES_ENGINE", raising=False)
    ran = []

    def recorder(name):
        def fn(data, output_dir=None, verbose=True, **kw):
            ran.append(name)
            return {"captured": 0, "failed": 0, "videos": 0, "engine": name}
        return fn

    monkeypatch.setattr(_cf, "capture_session_frames", recorder("stream"))
    monkeypatch.setattr(_cf, "capture_session_frames_local", recorder("local"))
    if mcp is not None:
        import ratelimit
        monkeypatch.setattr(mcp, "capture_session_frames", recorder("stream"))
        monkeypatch.setattr(mcp, "capture_session_frames_local", recorder("local"))
        monkeypatch.setattr(mcp, "DATA_DIR", tmp_path)
        monkeypatch.setattr(ratelimit, "status", lambda *a, **k: {"blocked": False, "seconds_left": 0})
    return _chooser_session(tmp_path), ran, mcp


def _run_cli(monkeypatch, sdir, *extra):
    monkeypatch.setattr(sys, "argv", ["capture_frames.py", "--session", str(sdir), "--json", *extra])
    _cf.main()


def _run_mcp(mcp, sdir, **kw):
    if mcp is None:
        pytest.skip("mcp_server not importable")
    return _json.loads(mcp.harvest_frames(str(sdir), **kw))


def test_chooser_a_no_env_no_explicit_is_local(chooser, monkeypatch):
    sdir, ran, mcp = chooser
    assert _cf.default_engine() == "local"
    _run_cli(monkeypatch, sdir)
    assert ran == ["local"]
    out = _run_mcp(mcp, sdir)
    assert ran == ["local", "local"] and out["engine"] == "local"


def test_chooser_b_env_stream_is_stream(chooser, monkeypatch):
    sdir, ran, mcp = chooser
    monkeypatch.setenv("CINOPSIS_FRAMES_ENGINE", "  Stream ")   # case-insensitive, trimmed
    assert _cf.default_engine() == "stream"
    _run_cli(monkeypatch, sdir)
    assert ran == ["stream"]
    out = _run_mcp(mcp, sdir)
    assert ran == ["stream", "stream"] and out["engine"] == "stream"


@pytest.mark.parametrize("env_value,explicit", [("stream", "local"), ("local", "stream")])
def test_chooser_c_explicit_wins_over_env(chooser, monkeypatch, env_value, explicit):
    sdir, ran, mcp = chooser
    monkeypatch.setenv("CINOPSIS_FRAMES_ENGINE", env_value)
    _run_cli(monkeypatch, sdir, "--engine", explicit)
    assert ran == [explicit]
    out = _run_mcp(mcp, sdir, engine=explicit)
    assert ran == [explicit, explicit] and out["engine"] == explicit


def test_chooser_d_bogus_env_warns_once_and_is_local(chooser, monkeypatch, capsys):
    sdir, ran, mcp = chooser
    monkeypatch.setenv("CINOPSIS_FRAMES_ENGINE", "bogus")
    assert _cf.default_engine() == "local"
    err = capsys.readouterr().err.strip().splitlines()
    assert len(err) == 1 and "bogus" in err[0] and "CINOPSIS_FRAMES_ENGINE" in err[0]
    _run_cli(monkeypatch, sdir)
    assert ran == ["local"]
    assert len([l for l in capsys.readouterr().err.splitlines() if "bogus" in l]) == 1
    out = _run_mcp(mcp, sdir)
    assert ran == ["local", "local"] and out["engine"] == "local"


def test_chooser_e_single_frame_paths_stay_on_stream(tmp_path, monkeypatch):
    """compare_server /api/screenshot and MCP capture_frame still call the stream
    capture_frame and never read CINOPSIS_FRAMES_ENGINE (E3)."""
    # Import first: mcp_server binds default_engine under an alias at import time.
    compare_server = pytest.importorskip("compare_server")
    mcp = pytest.importorskip("mcp_server")
    monkeypatch.setenv("CINOPSIS_FRAMES_ENGINE", "local")
    monkeypatch.setenv("CINOPSIS_VIEWER_LIVE_FRAMES", "1")
    monkeypatch.setattr(_cf, "default_engine",
                        lambda *a, **k: pytest.fail("single-frame path consulted the chooser"))
    monkeypatch.setattr(mcp, "_default_frames_engine",
                        lambda *a, **k: pytest.fail("single-frame path consulted the chooser"))
    calls = []

    def fake_capture(video_id, timestamp, *a, **k):
        calls.append((video_id, int(timestamp)))
        return "aGk="

    monkeypatch.setattr(compare_server, "capture_frame", fake_capture)
    client = compare_server.create_app(tmp_path).test_client()
    resp = client.post("/api/screenshot", json={"video_id": _VID, "timestamp": 3, "live": True})
    assert resp.status_code == 200 and calls == [(_VID, 3)]

    monkeypatch.setattr(mcp, "_capture_frame", fake_capture)
    out = _json.loads(mcp.capture_frame(_VID, 4))
    assert out["status"] == "ok" and calls == [(_VID, 3), (_VID, 4)]


if __name__ == "__main__":
    unittest.main()
