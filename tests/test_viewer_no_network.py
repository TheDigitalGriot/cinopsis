"""cc5-batch2 leak 1 - opening the companion viewer makes zero network calls. Offline.

Measured on session 680c692d909a: opening the viewer fired 36 POST /api/screenshot, 24 cache
hits and 12 misses that fell through to a live stream-URL grab and 500'd. The contract now:
a miss is a clean 404 with a hint, a live grab is opt-in twice over (body live: true AND
CINOPSIS_VIEWER_LIVE_FRAMES=1) and even then runs behind ratelimit's frames gate.
"""
import json
import re
from pathlib import Path

import pytest

import capture_frames
import compare_server
import ratelimit

VIEWER = Path(__file__).resolve().parent.parent / "viewer" / "viewer.html"
REAL_GET_STREAM_URL = capture_frames.get_stream_url
REAL_CAPTURE_FRAME = capture_frames.capture_frame


@pytest.fixture
def env(tmp_path, monkeypatch):
    import _utils
    canonical, working = tmp_path / "canonical", tmp_path / "working"
    for d in (canonical / "frames", working / "frames", canonical / "sessions" / "s1"):
        d.mkdir(parents=True)
    monkeypatch.setattr(_utils, "DATA_DIR", working)
    monkeypatch.delenv("CINOPSIS_VIEWER_LIVE_FRAMES", raising=False)
    (canonical / "sessions" / "index.json").write_text(
        json.dumps([{"id": "sid1", "dir_name": "s1"}]), encoding="utf-8")
    (canonical / "sessions" / "s1" / "comparison_data.json").write_text(json.dumps({
        "videos": [{"id": "vidA"}],
        "analysis": {"key_moments": [{"video_id": "vidA", "timestamp": 7, "label": "x", "description": "y"}],
                     "workflow_steps": [{"video_id": "vidA", "t_start": 5, "frame_ref": "frames/vidA_5.png"}]}}),
        encoding="utf-8")
    net = []

    def no_net(*a, **k):
        net.append(a)
        raise AssertionError("network/subprocess call from the viewer path")
    # every road to the network: the stream-URL grab and raw subprocess (yt-dlp, ffmpeg)
    monkeypatch.setattr(capture_frames, "get_stream_url", no_net)
    monkeypatch.setattr(capture_frames.subprocess, "run", no_net)
    calls = []
    monkeypatch.setattr(compare_server, "capture_frame", lambda *a, **k: calls.append(a) or None)
    app = compare_server.create_app(canonical)
    app.testing = True
    return app.test_client(), canonical, working, net, calls


def test_viewer_open_sequence_makes_zero_network_calls(env):
    c, canonical, working, net, calls = env
    (working / "frames" / "vidA_7.png").write_bytes(b"km")
    for url in ("/", "/api/sessions", "/api/session/sid1", "/api/frames-index?video_ids=vidA"):
        assert c.get(url).status_code == 200, url
    assert net == [] and calls == []


def test_viewer_html_never_posts_screenshot_on_load():
    html = VIEWER.read_text(encoding="utf-8")
    posts = [m.start() for m in re.finditer(r"fetch\('/api/screenshot'", html)]
    assert len(posts) == 1, "exactly one POST site: the explicit Edit-mode capture"
    assert html.startswith("function captureFrame(", html.rfind("function ", 0, posts[0]))
    # captureFrame is reached only from the Edit-mode timeline click, never from session load
    callers = [m.start() for m in re.finditer(r"captureFrame\(", html)]
    assert len(callers) == 2                                           # one call + the definition
    assert "if (!editMode)" in html[callers[0] - 400:callers[0]]
    auto = html[html.index("function autoFetchScreenshots()"):html.index("/* ═══ LIBRARY MODAL")]
    assert "/api/screenshot" not in auto and "/api/frames-index" in auto


def test_cache_miss_returns_404_and_never_calls_get_stream_url(env):
    c, _, _, net, calls = env
    r = c.post("/api/screenshot", json={"video_id": "vidA", "timestamp": 99, "session": "sid1"})
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "frame-not-captured"
    assert body["hint"] == "capture_frames.py --engine local --session s1"
    assert net == [] and calls == []


def test_cache_hit_in_either_home_serves_the_frame(env):
    """The 12 measured misses were frames that existed in the working home while the route
    searched only the canonical one. Both homes are searched now, as /frames/ always did."""
    c, canonical, working, net, calls = env
    (working / "frames" / "vidA_7.png").write_bytes(b"working-home")
    (canonical / "frames" / "vidA_5.png").write_bytes(b"canonical-home")
    r1 = c.post("/api/screenshot", json={"video_id": "vidA", "timestamp": 7.9})
    r2 = c.post("/api/screenshot", json={"video_id": "vidA", "timestamp": 5})
    assert r1.status_code == 200 and r1.get_json()["frame_ref"] == "frames/vidA_7.png"
    assert r2.status_code == 200 and r2.get_json()["frame_ref"] == "frames/vidA_5.png"
    assert net == [] and calls == []


def test_frame_ref_in_body_is_served_and_cannot_escape(env):
    c, _, working, net, calls = env
    (working / "frames" / "vidA_5.png").write_bytes(b"ref")
    r = c.post("/api/screenshot", json={"video_id": "vidA", "timestamp": 1, "frame_ref": "frames/vidA_5.png"})
    assert r.status_code == 200
    r = c.post("/api/screenshot", json={"video_id": "vidA", "timestamp": 1, "frame_ref": "../../secret.png"})
    assert r.status_code == 404 and net == [] and calls == []


def test_live_flag_without_env_is_refused(env):
    c, _, _, net, calls = env
    r = c.post("/api/screenshot", json={"video_id": "vidA", "timestamp": 99, "live": True})
    assert r.status_code == 404 and r.get_json()["error"] == "frame-not-captured"
    assert calls == [] and net == []


def test_env_without_live_flag_is_refused(env, monkeypatch):
    c, _, _, net, calls = env
    monkeypatch.setenv("CINOPSIS_VIEWER_LIVE_FRAMES", "1")
    r = c.post("/api/screenshot", json={"video_id": "vidA", "timestamp": 99})
    assert r.status_code == 404 and calls == [] and net == []


def test_explicit_live_grab_goes_through_the_frames_gate(env, monkeypatch):
    """live: true + env opt-in reaches the REAL capture_frame -> get_stream_url, whose frames
    gate refuses while cooling WITHOUT touching subprocess (still guarded by the fixture)."""
    c, _, _, net, _ = env
    monkeypatch.setenv("CINOPSIS_VIEWER_LIVE_FRAMES", "1")
    monkeypatch.setattr(compare_server, "capture_frame", REAL_CAPTURE_FRAME)
    monkeypatch.setattr(capture_frames, "get_stream_url", REAL_GET_STREAM_URL)
    gate = []

    def cooling(source="fetch", door=None):
        gate.append(source)
        raise ratelimit.RateLimited(0, "test cooldown")
    monkeypatch.setattr(ratelimit, "check_gate", cooling)
    r = c.post("/api/screenshot", json={"video_id": "vidA", "timestamp": 99, "live": True})
    assert r.status_code == 502 and r.get_json()["error"] == "live-grab-failed"
    assert gate == ["frames"]
    assert net == []                               # subprocess.run never reached


def test_frames_index_lists_both_homes_disk_only(env):
    c, canonical, working, net, calls = env
    (canonical / "frames" / "vidA_5.png").write_bytes(b"a")
    (working / "frames" / "vidA_12.png").write_bytes(b"b")
    (working / "frames" / "vidA_notanint.png").write_bytes(b"c")
    (working / "frames" / "other_3.png").write_bytes(b"d")
    r = c.get("/api/frames-index?video_ids=vidA,nobody")
    assert r.get_json() == {"vidA": [5, 12], "nobody": []}
    assert net == [] and calls == []
