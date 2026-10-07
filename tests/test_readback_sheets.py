"""readback_sheets.py: 3x3 contact sheets + manifest, offline, with tiny generated PNGs."""
import json
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import readback_sheets as rs


def _session(tmp_path, n_a=11, n_b=2, missing=(3,)):
    frames = tmp_path / "frames"
    frames.mkdir()
    steps = []
    for vid, n in (("vidAAAAAAAA", n_a), ("vidBBBBBBBB", n_b)):
        for i in range(n, 0, -1):          # reversed: the tool must sort by index
            t = 10 * i
            ref = f"frames/{vid}_{t}.png"
            if not (vid == "vidAAAAAAAA" and i in missing):
                Image.new("RGB", (64, 36), (i * 20 % 255, 80, 160)).save(tmp_path / ref)
            steps.append({"video_id": vid, "index": i, "t_start": t, "action": f"step {i}",
                          "ui_kind": "button", "ui_target": f"B{i}", "frame_ref": ref})
    steps.append({"video_id": "vidBBBBBBBB", "index": 3, "t_start": 99, "action": "no frame",
                  "ui_kind": "tab", "ui_target": "T", "frame_ref": None})
    sj = tmp_path / "comparison_data.json"
    sj.write_text(json.dumps({"analysis": {"workflow_steps": steps}}), encoding="utf-8")
    return sj


def _run(tmp_path, monkeypatch, **kw):
    monkeypatch.setattr(rs, "DATA", tmp_path)
    sj = _session(tmp_path)
    return rs.build_sheets(sj, tmp_path / "out", **kw), tmp_path / "out"


def test_sheet_count_and_names(tmp_path, monkeypatch):
    m, out = _run(tmp_path, monkeypatch)
    assert m["videos"]["vidAAAAAAAA"]["sheets"] == ["vidAAAAAAAA_sheet_01.png", "vidAAAAAAAA_sheet_02.png"]
    assert m["videos"]["vidBBBBBBBB"]["sheets"] == ["vidBBBBBBBB_sheet_01.png"]
    assert all((out / s["sheet"]).is_file() for s in m["sheets"])
    assert json.loads((out / "manifest.json").read_text(encoding="utf-8")) == m


def test_tiles_in_index_order_with_positions(tmp_path, monkeypatch):
    m, _ = _run(tmp_path, monkeypatch)
    first = m["sheets"][0]["tiles"]
    assert [t["index"] for t in first] == list(range(1, 10))
    assert (first[4]["row"], first[4]["col"]) == (1, 1)
    assert first[0]["t_start"] == 10 and first[0]["ui_target"] == "B1" and first[0]["action"] == "step 1"
    assert [t["index"] for t in m["sheets"][1]["tiles"]] == [10, 11]


def test_missing_frames_become_labelled_blanks(tmp_path, monkeypatch):
    m, _ = _run(tmp_path, monkeypatch)
    flags = {(t["video_id"], t["index"]): t["frame_missing"] for s in m["sheets"] for t in s["tiles"]}
    assert flags[("vidAAAAAAAA", 3)] is True
    assert flags[("vidBBBBBBBB", 3)] is True       # frame_ref None
    assert flags[("vidAAAAAAAA", 1)] is False


def test_sheet_geometry(tmp_path, monkeypatch):
    m, out = _run(tmp_path, monkeypatch, tile_width=100)
    with Image.open(out / "vidAAAAAAAA_sheet_01.png") as im:
        assert im.size == (3 * 100 + 2 * rs.GAP, 3 * round(100 * rs.ASPECT) + 2 * rs.GAP)
    with Image.open(out / "vidAAAAAAAA_sheet_02.png") as im:   # 2 tiles -> one row
        assert im.size[1] == round(100 * rs.ASPECT)


def test_label_is_burnt_into_corner(tmp_path):
    src = tmp_path / "f.png"
    Image.new("RGB", (200, 112), (255, 255, 255)).save(src)
    tile, missing = rs.make_tile(src, "#7  t42", 200)
    assert not missing
    assert tile.getpixel((1, 1)) == rs.LABEL_BG
    assert tile.getpixel((199, 111)) == (255, 255, 255)


def test_per_sheet_option(tmp_path, monkeypatch):
    m, _ = _run(tmp_path, monkeypatch, per_sheet=4)
    assert len(m["videos"]["vidAAAAAAAA"]["sheets"]) == 3
    assert m["cols"] == 2


def test_cli(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(rs, "DATA", tmp_path)
    sj = _session(tmp_path)
    assert rs.main(["--session", str(sj), "--out", str(tmp_path / "o")]) == 0
    assert "READBACK_SHEETS_OK" in capsys.readouterr().out
    assert rs.main(["--session", str(tmp_path / "nope")]) == 2
