"""v3.0.0 R5 - harvest breaks B7-B12 and the /frames route (B2, server half). Offline."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import build_session_from_analysis as bsa
import compare_server
import compare_videos as cv
import verify_invariants as vi

VIDEOS = [{"id": "v1", "chapters": [{"start_time": 0, "end_time": 60, "title": "Setup"},
                                     {"start_time": 60, "end_time": 300, "title": "Build"}]},
          {"id": "v2"}]


def test_b9_derive_stats_always_counts_the_arrays_including_steps():
    analysis = {"topics": [1, 2], "disagreements": [], "key_moments": [1],
                "workflow_steps": [{"video_id": "v1"}] * 3}
    stats = cv.derive_stats(VIDEOS, analysis, {"key_moments": 99, "extra": "kept"})
    assert stats == {"extra": "kept", "total_videos": 2, "common_topics": 2, "disagreements": 0,
                     "key_moments": 1, "workflow_steps": 3}


def test_b9_build_session_knows_workflow_steps(monkeypatch):
    monkeypatch.setattr(cv, "generate_session_id", lambda: "sid")
    data = {"title": "t", "videos": [dict(v) for v in VIDEOS],
            "analysis": {"workflow_steps": [{"video_id": "v1", "index": 1, "t_start": 75, "phase": None}]},
            "stats": {"workflow_steps": 7}}
    out = bsa.build(data)
    assert out["stats"]["workflow_steps"] == 1                              # recomputed, not carried
    assert out["analysis"]["workflow_steps"][0]["phase"] == "Build"        # B12 via build()


def test_b12_fill_phases_fills_nulls_and_reports_mismatches_without_overwriting():
    analysis = {"workflow_steps": [
        {"video_id": "v1", "index": 1, "t_start": 10, "phase": None},
        {"video_id": "v1", "index": 2, "t_start": 70, "phase": "Deploy"},
        {"video_id": "v2", "index": 1, "t_start": 5, "phase": None}]}
    mism = cv.fill_phases(VIDEOS, analysis)
    steps = analysis["workflow_steps"]
    assert steps[0]["phase"] == "Setup" and steps[1]["phase"] == "Deploy" and steps[2]["phase"] is None
    assert len(mism) == 1 and "'Deploy'" in mism[0] and "'Build'" in mism[0]


def test_b8_add_videos_keeps_steps_and_recomputes_stats(monkeypatch, tmp_path):
    data = {"session": {"id": "sid", "video_count": 1}, "videos": [{"id": "v1"}],
            "analysis": {"unified_summary": "x", "topics": [1], "disagreements": [1], "key_moments": [1, 2],
                         "workflow_steps": [{"video_id": "v1"}]},
            "stats": {"total_videos": 1, "key_moments": 2, "workflow_steps": 1}}
    sessions = tmp_path / "sessions"
    (sessions / "s1").mkdir(parents=True)
    (sessions / "index.json").write_text(json.dumps([{"id": "sid", "dir_name": "s1"}]), encoding="utf-8")
    (sessions / "s1" / "comparison_data.json").write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(cv, "SESSIONS_DIR", sessions)
    captured = {}
    monkeypatch.setattr(cv, "update_session", lambda sid, d: captured.update(d) or d)
    cv.add_videos_to_session("sid", [{"id": "v2"}])
    assert captured["analysis"]["workflow_steps"] == [{"video_id": "v1"}]
    assert captured["analysis"]["key_moments"] == []
    assert captured["stats"]["key_moments"] == 0 and captured["stats"]["workflow_steps"] == 1
    assert captured["stats"]["total_videos"] == 2


def test_b10_steps_alone_count_as_analysis():
    assert compare_server._has_analysis({"analysis": {"workflow_steps": [{"video_id": "v1"}]}})
    assert not compare_server._has_analysis({"analysis": {}, "videos": []})


def test_b11_inv2_checks_step_membership():
    session = SimpleNamespace(label="store/s1", videos=[{"id": "v1", "transcript": [{"start": 0, "text": "x"}]}],
                              analysis={"workflow_steps": [{"video_id": "v1"}, {"video_id": "ghost"}]})
    violations, _ = vi.check_digest_real([session], SimpleNamespace(transcripts=set(), descriptions=set()))
    assert len(violations) == 1 and "ghost" in violations[0] and "workflow_step" in violations[0]


@pytest.fixture
def client(tmp_path, monkeypatch):
    import _utils
    canonical = tmp_path / "canonical"
    working = tmp_path / "working"
    (canonical / "frames").mkdir(parents=True)
    (working / "frames").mkdir(parents=True)
    (canonical / "sessions").mkdir()
    monkeypatch.setattr(_utils, "DATA_DIR", working)
    app = compare_server.create_app(canonical)
    app.testing = True
    return app.test_client(), canonical, working


def test_b7_screenshot_rejects_bad_timestamps_with_400(client):
    c, _, _ = client
    for ts in ("abc", None, -3):
        r = c.post("/api/screenshot", json={"video_id": "dQw4w9WgXcQ", "timestamp": ts})
        assert r.status_code == 400, ts


def test_b2_frames_route_serves_both_homes_and_refuses_traversal(client):
    c, canonical, working = client
    (canonical / "frames" / "a_1.png").write_bytes(b"canon")
    (working / "frames" / "b_2.png").write_bytes(b"work")
    assert c.get("/frames/a_1.png").data == b"canon"
    assert c.get("/frames/frames/b_2.png").data == b"work"          # frame_ref form
    assert c.get("/frames/missing.png").status_code == 404
    assert c.get("/frames/..%2F..%2Fsecret.txt").status_code in (400, 404)


def test_b1_promotion_carries_cited_frames_to_canonical(tmp_path):
    import persist_session as ps
    work, canon = tmp_path / "work", tmp_path / "canon"
    (work / "sessions" / "s1").mkdir(parents=True)
    (work / "frames").mkdir()
    (work / "frames" / "v1_75.png").write_bytes(b"png")
    data = {"session": {"id": "sid", "title": "t", "created_at": "x"}, "videos": [],
            "analysis": {"workflow_steps": [{"video_id": "v1", "frame_ref": "frames/v1_75.png"},
                                            {"video_id": "v1", "frame_ref": "frames/../escape.png"},
                                            {"video_id": "v1", "frame_ref": None}]}}
    (work / "sessions" / "s1" / "comparison_data.json").write_text(json.dumps(data), encoding="utf-8")
    ps.persist_session("s1", work / "sessions", canon / "sessions")
    assert (canon / "frames" / "v1_75.png").read_bytes() == b"png"
    assert not (canon / "escape.png").exists()


VIEWER = Path(__file__).resolve().parent.parent / "viewer" / "viewer.html"


def test_viewer_b2_b5_b6_b13_are_wired():
    html = VIEWER.read_text(encoding="utf-8")
    assert "function frameUrl(ref)" in html and 'class="frm-img"' in html                     # B2
    assert "buildTimeline(v, moments, dur, stepsFor(a, v))" in html and "marker step" in html  # B5
    assert "moment + step density" in html and "<b>moment density</b>" not in html            # B5 hint x2
    # B6 superseded by cc5-batch2 leak 1: steps keep their harvested frame_ref and moments/topics
    # read the disk-only /api/frames-index; nothing POSTs /api/screenshot on open.
    assert "localFrames[k] = frameUrl('frames/' + k" in html                                    # B6
    assert "statTile('Workflow steps', steps.length" in html and "stats says " in html        # B13
    assert "stats.key_moments = a.key_moments.length" in html                                  # B4 (count)
