"""backfill_catchups digest overlay: applied only where a cached transcript backs it (INV2)."""
import json

import backfill_catchups as bc


def _video(vid, takeaway="src takeaway"):
    return bc.make_video(vid, "T", "C", takeaway, {"core_takeaway": takeaway})


OVERLAY = {
    "AAAAAAAAAAA": {"core_takeaway": "From transcript.", "key_points": ["p1", "p2", "p3"],
                    "why_it_matters": "Because.", "digest_source": "transcript"},
    "BBBBBBBBBBB": {"core_takeaway": "x", "key_points": ["y"], "why_it_matters": "z"},
    "ZZZZZZZZZZZ": {"core_takeaway": "x", "key_points": ["y"], "why_it_matters": "z"},
}


def test_overlay_applies_only_with_cached_transcript():
    videos = [_video("AAAAAAAAAAA"), _video("BBBBBBBBBBB")]
    applied, refused, unmatched = bc.apply_digest_overlay(videos, OVERLAY, {"AAAAAAAAAAA"})
    assert applied == ["AAAAAAAAAAA"]
    assert refused == ["BBBBBBBBBBB"]
    assert unmatched == ["ZZZZZZZZZZZ"]
    a, b = videos
    assert a["digest"] == {"core_takeaway": "From transcript.", "key_points": ["p1", "p2", "p3"],
                           "why_it_matters": "Because."}
    assert a["digest_source"] == "transcript"
    # no transcript -> source takeaway kept, nothing padded
    assert b["digest"] == {"core_takeaway": "src takeaway", "key_points": [], "why_it_matters": ""}
    assert "digest_source" not in b


def test_quality_flag_carried():
    videos = [_video("AAAAAAAAAAA")]
    ov = {"AAAAAAAAAAA": dict(OVERLAY["AAAAAAAAAAA"], quality_flag="short transcript")}
    bc.apply_digest_overlay(videos, ov, {"AAAAAAAAAAA"})
    assert videos[0]["quality_flag"] == "short transcript"


def test_load_overlay_missing_and_wrong_day(tmp_path):
    assert bc.load_digest_overlay("2026-08-20", tmp_path / "none.json") == {}
    p = tmp_path / "o.json"
    p.write_text(json.dumps({"day": "2026-08-16", "videos": {}}), encoding="utf-8")
    try:
        bc.load_digest_overlay("2026-08-20", p)
    except ValueError:
        pass
    else:
        raise AssertionError("wrong-day overlay must be refused")
