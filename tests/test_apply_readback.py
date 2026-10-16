"""scripts/apply_readback.py (promoted from .prism/local/cc5-batch4 by N1, 2026-10-15).

Denial reads the structured `contradicts` boolean, never the note (drift "Read-back regex misses
frame contradictions"); a shown step with no boolean is refused; every applied field is re-checked
against comparison-schema.md; the session and its frames resolve under CLAUDE_PLUGIN_DATA.
Network-free: a fixture session in tmp_path.
"""
import importlib
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import apply_readback as ar  # noqa: E402
import readback_sheets as rs  # noqa: E402

VID = "vidAAAAAAAA"


def _step(i, t, **kw):
    s = {"video_id": VID, "index": i, "t_start": t, "t_end": t + 5, "phase": None,
         "action": f"Do {i}", "app": "CC5", "ui_path": ["Panel"], "ui_kind": "button",
         "ui_options": [], "ui_target": f"B{i}", "parameters": {"Strength": "1"}, "result": "r",
         "frame_ref": f"frames/{VID}_{t}.png", "confidence": "spoken"}
    s.update(kw)
    return s


@pytest.fixture
def store(tmp_path):
    """<root>/sessions/S/comparison_data.json with frames under <root>/frames, like the real store."""
    root = tmp_path / "store"
    sdir = root / "sessions" / "S"
    sdir.mkdir(parents=True)
    (root / "frames").mkdir()
    steps = [_step(i, 10 * i) for i in range(1, 10)]
    steps[7]["frame_ref"] = f"frames/{VID}_missing.png"           # step 8: no frame on disk
    for s in steps:
        if "missing" not in s["frame_ref"]:
            (root / s["frame_ref"]).write_bytes(b"png")
    data = {"videos": [{"id": VID}], "analysis": {"workflow_steps": steps}}
    (sdir / "comparison_data.json").write_text(json.dumps(data), encoding="utf-8")
    return root, sdir


def _ok(i, t, **kw):
    p = {"index": i, "t_start": t, "shown": True, "contradicts": False, "contradicts_reason": "",
         "note": "control visible"}
    p.update(kw)
    return p


def _patch(sdir, steps, name=f"readback_{VID}.json", vid=VID):
    (sdir / name).write_text(json.dumps({"video_id": vid, "steps": steps}), encoding="utf-8")


def _session(sdir):
    data = json.loads((sdir / "comparison_data.json").read_text(encoding="utf-8"))
    return {s["index"]: s for s in data["analysis"]["workflow_steps"]}


def test_contradicts_field_denies_and_note_wording_is_ignored(store):
    root, sdir = store
    _patch(sdir, [
        _ok(1, 10),                                                  # clean -> shown
        # worded so the old regex could never match it: only the field denies it
        _ok(2, 20, contradicts=True, contradicts_reason="slider sits at 0.2, step says 0.5",
            note="slider sits at its default"),
        # the old regex WOULD have denied this note; the field says it is fine -> shown
        _ok(3, 30, note="Strength field still on screen, as the step says"),
        _ok(4, 40, contradicts="no"),                                # not a boolean -> refused
        {"index": 5, "t_start": 50, "shown": True, "note": "looks right"},  # no field -> refused
        {"index": 6, "t_start": 60, "shown": False, "contradicts": True,
         "contradicts_reason": "before-action: menu not yet open", "note": "x"},
        _ok(7, 70, contradicts=True, contradicts_reason="   "),     # blank reason still denies
    ])
    rep = ar.apply_readback(sdir / "comparison_data.json")[VID]
    after = _session(sdir)
    assert [i for i in after if after[i]["confidence"] == "shown"] == [1, 3]
    assert rep["upgraded_to_shown"] == 2
    assert any(d.startswith("#2 t20: slider sits at 0.2") for d in rep["kept_frame_contradicts"])
    assert any(d.startswith("#7 t70: contradicts with no reason") for d in rep["kept_frame_contradicts"])
    assert "#4: no structured contradicts boolean" in rep["refused"]
    assert "#5: no structured contradicts boolean" in rep["refused"]
    assert rep["frame_before_action"] == ["#6 t60"]
    assert after[6]["confidence"] == "spoken"


def test_structured_value_clash_still_denies(store):
    _, sdir = store
    _patch(sdir, [_ok(1, 10, parameters={"Strength": "9"}), _ok(2, 20, parameters={"On screen": "3"})])
    rep = ar.apply_readback(sdir / "comparison_data.json")[VID]
    assert rep["upgraded_to_shown"] == 0 and len(rep["kept_frame_contradicts"]) == 2


def test_schema_checked_apply(store):
    _, sdir = store
    _patch(sdir, [
        _ok(1, 10, ui_kind="knob"),                                   # enum violation
        _ok(2, 20, ui_options=["A", "B"]),                           # options on a button
        _ok(3, 30, app="Maya"),                                       # app enum
        _ok(4, 40, parameters={"Size": 5}),                           # non-string value
        _ok(5, 50, ui_kind="dropdown", ui_options=["Low", "High"], parameters={"Size": "5"},
            ui_target="Quality", ui_path=["Render", "Quality"]),      # valid -> applied
        _ok(8, 80),                                                   # no frame on disk
        _ok(9, 999),                                                  # t_start mismatch
    ])
    rep = ar.apply_readback(sdir / "comparison_data.json")[VID]
    after = _session(sdir)
    assert rep["upgraded_to_shown"] == 1
    s5 = after[5]
    assert (s5["confidence"], s5["ui_kind"], s5["ui_options"], s5["ui_target"]) == \
           ("shown", "dropdown", ["Low", "High"], "Quality")
    assert s5["parameters"] == {"Strength": "1", "Size": "5"}       # merged, not replaced
    assert all(after[i]["confidence"] == "spoken" for i in (1, 2, 3, 4, 8, 9))
    refused = " | ".join(rep["refused"])
    for frag in ("ui_kind 'knob'", "ui_options on button", "app 'Maya'", "#4: parameters",
                 "#8: shown without a frame on disk", "#9: index/t_start mismatch"):
        assert frag in refused


def test_chunks_concatenate_and_mismatched_video_id_raises(store):
    _, sdir = store
    _patch(sdir, [_ok(1, 10)], name=f"readback_{VID}_p1.json")
    _patch(sdir, [_ok(2, 20)], name=f"readback_{VID}_p2.json")
    assert ar.patched_ids(sdir) == [VID]
    assert ar.apply_readback(sdir / "comparison_data.json")[VID]["upgraded_to_shown"] == 2
    _patch(sdir, [_ok(3, 30)], name=f"readback_{VID}_p3.json", vid="other")
    with pytest.raises(ar.PatchError):
        ar.apply_readback(sdir / "comparison_data.json", ids=[VID])


def test_cli_session_by_name_under_data_dir_and_dry_run(store, monkeypatch, capsys):
    root, sdir = store
    monkeypatch.setattr(rs, "DATA", root)
    _patch(sdir, [_ok(1, 10)])
    before = (sdir / "comparison_data.json").read_text(encoding="utf-8")
    assert ar.main(["--session", "S", "--dry-run"]) == 0
    assert json.loads(capsys.readouterr().out)[VID]["upgraded_to_shown"] == 1
    assert (sdir / "comparison_data.json").read_text(encoding="utf-8") == before
    assert ar.main(["--session", "S", VID]) == 0
    assert _session(sdir)[1]["confidence"] == "shown"
    assert ar.main(["--session", "nope"]) == 2


def test_honours_claude_plugin_data(tmp_path, monkeypatch):
    import _utils
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
    try:
        importlib.reload(_utils)
        importlib.reload(rs)
        assert rs.DATA == tmp_path
        loose = tmp_path / "elsewhere" / "comparison_data.json"
        assert rs.data_root_for(loose) == tmp_path                   # not a sessions/<name> layout
        nested = tmp_path / "other_store" / "sessions" / "X" / "comparison_data.json"
        assert rs.data_root_for(nested) == (tmp_path / "other_store").resolve()
    finally:
        monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
        importlib.reload(_utils)
        importlib.reload(rs)
