"""validate_comparison.py: the full comparison-schema.md contract, every violation named."""
import copy
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import validate_comparison as vc


def _step(vid="aaaaaaaaaaa", index=1, t_start=10, t_end=20, phase="Intro", **kw):
    s = {"video_id": vid, "index": index, "t_start": t_start, "t_end": t_end, "phase": phase,
         "action": "Open the Physics tab", "app": "CC5", "ui_path": ["Modify", "Physics"],
         "ui_kind": "tab", "ui_target": "Physics", "ui_options": [], "parameters": {},
         "result": "Physics settings appear", "frame_ref": None, "confidence": "spoken"}
    s.update(kw)
    return s


def _session():
    return {
        "session": {"id": "x", "title": "t"},
        "videos": [{
            "id": "aaaaaaaaaaa", "title": "Spring bones in CC5", "summary": "A synopsis.",
            "digest": {"core_takeaway": "Takeaway.", "key_points": ["One"], "why_it_matters": "Because."},
            "chapters": [{"title": "Intro", "start_time": 0, "end_time": 60},
                         {"title": "Setup", "start_time": 60, "end_time": 300}],
        }, {
            "id": "bbbbbbbbbbb", "title": "Hair physics", "summary": "Another.",
            "digest": {"core_takeaway": "T.", "key_points": ["P"], "why_it_matters": "W."},
            "chapters": [],
        }],
        "analysis": {
            "unified_summary": "Both cover physics.",
            "topics": [{"name": "Spring bones", "video_coverage": ["aaaaaaaaaaa", "bbbbbbbbbbb"],
                        "consensus": "agreement",
                        "entries": [{"video_id": "aaaaaaaaaaa", "timestamp": 12, "quote": "q"},
                                    {"video_id": "bbbbbbbbbbb", "timestamp": 5, "quote": "q"}]}],
            "disagreements": [{"topic": "Bake", "positions": [
                {"video_id": "aaaaaaaaaaa", "position": "bake"},
                {"video_id": "bbbbbbbbbbb", "position": "live"}]}],
            "key_moments": [{"video_id": "aaaaaaaaaaa", "timestamp": 30, "label": "L", "description": "Why."}],
            "workflow_steps": [_step(), _step(index=2, t_start=70, t_end=90, phase="Setup"),
                               _step(vid="bbbbbbbbbbb", phase=None)],
        },
        "stats": {"common_topics": 1, "disagreements": 1, "key_moments": 1, "workflow_steps": 3},
    }


def _has(errs, needle):
    assert any(needle in e for e in errs), errs


def test_valid_session_passes():
    assert vc.validate(_session()) == []


@pytest.mark.parametrize("mutate,needle", [
    (lambda d: d["videos"][0].update(title="Unknown"), "unresolved title"),
    (lambda d: d["videos"][0]["digest"].update(key_points=[]), "key_points"),
    (lambda d: d["videos"][0].pop("chapters"), "chapters missing"),
    (lambda d: d["videos"][0]["chapters"][0].update(start_time="0"), "chapters[0]"),
    (lambda d: d["analysis"]["topics"][0].update(consensus="mixed"), "consensus"),
    (lambda d: d["analysis"]["topics"][0].update(video_coverage=[0, 1]), "array of video id strings"),
    (lambda d: d["analysis"]["topics"][0].update(video_coverage=["aaaaaaaaaaa", "zzz"]), "not in videos[]"),
    (lambda d: d["analysis"]["disagreements"][0].update(creator_a="x"), "exactly"),
    (lambda d: d["analysis"]["disagreements"][0]["positions"][0].update(stance="x"),
     "exactly {video_id, position}"),
    (lambda d: d["analysis"]["key_moments"][0].update(t_start=30), "merged with workflow_steps"),
    (lambda d: d["analysis"]["workflow_steps"][0].pop("frame_ref"), "missing ['frame_ref']"),
    (lambda d: d["analysis"]["workflow_steps"][0].update(extra=1), "extra ['extra']"),
    (lambda d: d["analysis"]["workflow_steps"][1].update(index=3), "contiguous"),
    (lambda d: d["analysis"]["workflow_steps"][0].update(index=True), "index must be an int"),
    (lambda d: d["analysis"]["workflow_steps"][0].update(t_end=10), "span"),
    (lambda d: d["analysis"]["workflow_steps"][0].update(t_start=10.5), "must be ints"),
    (lambda d: d["analysis"]["workflow_steps"][0].update(phase="Setup"), "phase"),
    (lambda d: d["analysis"]["workflow_steps"][2].update(phase="Intro"), "phase"),
    (lambda d: d["analysis"]["workflow_steps"][0].update(app="Maya"), "app"),
    (lambda d: d["analysis"]["workflow_steps"][0].update(ui_kind="toggle"), "ui_kind"),
    (lambda d: d["analysis"]["workflow_steps"][0].update(ui_options=["A"]), "ui_options must be []"),
    (lambda d: d["analysis"]["workflow_steps"][0].update(parameters={"Damping": 0.5}), "parameters"),
    (lambda d: d["analysis"]["workflow_steps"][0].update(frame_ref="data:image/png;base64,AAAA"), "frame_ref"),
    (lambda d: d["analysis"]["workflow_steps"][0].update(frame_ref="C:/x/frames/a.png"), "frame_ref"),
    (lambda d: d["analysis"]["workflow_steps"][0].update(frame_ref="../frames/a.png"), "frame_ref"),
    (lambda d: d["analysis"]["workflow_steps"][0].update(confidence="shown"), "shown without a frame_ref"),
    (lambda d: d["analysis"]["workflow_steps"][0].update(confidence="seen"), "confidence"),
    (lambda d: d["stats"].update(workflow_steps=2), "stats.workflow_steps"),
    (lambda d: d["stats"].update(key_moments="1"), "stats.key_moments"),
])
def test_each_violation_is_named(mutate, needle):
    d = copy.deepcopy(_session())
    mutate(d)
    _has(vc.validate(d), needle)


def test_dropdown_may_carry_options():
    d = _session()
    d["analysis"]["workflow_steps"][0].update(ui_kind="dropdown", ui_options=["Hair", "Cloth"])
    assert vc.validate(d) == []


def test_every_violation_reported_not_just_first():
    d = _session()
    d["analysis"]["workflow_steps"][0].update(app="Maya", ui_kind="toggle", confidence="seen")
    assert len(vc.validate(d)) >= 3


def test_malformed_never_raises():
    assert vc.validate({"videos": [None], "analysis": {"workflow_steps": [None, {}]}, "stats": []})
    assert vc.validate([]) == ["top level is not an object"]


def test_require_per_video():
    _has(vc.validate(_session(), require_per_video=True), "bbbbbbbbbbb: zero key_moments")


def test_check_frames_on_disk(tmp_path):
    d = _session()
    d["analysis"]["workflow_steps"][0].update(frame_ref="frames/aaaaaaaaaaa_10.png", confidence="shown")
    _has(vc.validate(d, data_dir=tmp_path), "does not exist")
    (tmp_path / "frames").mkdir()
    (tmp_path / "frames" / "aaaaaaaaaaa_10.png").write_bytes(b"png")
    assert vc.validate(d, data_dir=tmp_path) == []


def test_cli_exit_codes(tmp_path):
    sdir = tmp_path / "sessions" / "s1"
    sdir.mkdir(parents=True)
    f = sdir / "comparison_data.json"
    f.write_text(json.dumps(_session()), encoding="utf-8")
    assert vc.main(["--session", str(sdir)]) == 0
    bad = _session()
    bad["stats"]["workflow_steps"] = 9
    f.write_text(json.dumps(bad), encoding="utf-8")
    assert vc.main(["--session", str(sdir)]) == 1
    f.write_text("{not json", encoding="utf-8")
    assert vc.main(["--session", str(f)]) == 2


def test_cli_json_names_violations(tmp_path, capsys):
    f = tmp_path / "comparison_data.json"
    bad = _session()
    bad["analysis"]["topics"][0]["consensus"] = "mixed"
    f.write_text(json.dumps(bad), encoding="utf-8")
    assert vc.main(["--session", str(f), "--json"]) == 1
    verdict = json.loads(capsys.readouterr().out)
    assert verdict["ok"] is False and any("consensus" in v for v in verdict["violations"])
