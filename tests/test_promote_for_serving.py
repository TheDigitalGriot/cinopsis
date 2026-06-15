import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import compare_server as cs

EMPTY = {"unified_summary": "", "topics": [], "disagreements": [], "key_moments": []}
FULL = {"unified_summary": "It compares X and Y.", "topics": [{"name": "t"}],
        "disagreements": [], "key_moments": [{"video_id": "v1"}]}


def _write_session(sessions, dir_name, sid, analysis):
    d = Path(sessions) / dir_name
    d.mkdir(parents=True, exist_ok=True)
    data = {"session": {"id": sid, "title": "T", "created_at": "2026-06-13T10:00:00", "video_count": 1},
            "videos": [{"id": "v1", "thumbnail_base64": "x", "digest": {}}],
            "analysis": analysis, "stats": {}}
    (d / "comparison_data.json").write_text(json.dumps(data), encoding="utf-8")
    idx = Path(sessions) / "index.json"
    cur = json.loads(idx.read_text(encoding="utf-8")) if idx.exists() else []
    cur = [e for e in cur if e.get("id") != sid]
    cur.insert(0, {"id": sid, "title": "T", "created_at": "2026-06-13T10:00:00",
                   "video_count": 1, "dir_name": dir_name})
    idx.write_text(json.dumps(cur), encoding="utf-8")


class TestPromoteForServing(unittest.TestCase):
    def setUp(self):
        self.work = Path(tempfile.mkdtemp()) / "sessions"
        self.canon = Path(tempfile.mkdtemp()) / "sessions"

    def test_has_analysis_helper(self):
        self.assertFalse(cs._has_analysis({"analysis": EMPTY, "videos": []}))
        self.assertTrue(cs._has_analysis({"analysis": FULL, "videos": []}))

    def test_promotes_enriched_working_over_empty_canonical(self):
        # The bug: canonical was frozen empty at creation; working got the analysis.
        _write_session(self.work, "2026-06-13_x", "id1", FULL)
        _write_session(self.canon, "2026-06-13_x", "id1", EMPTY)
        cs._promote_session_for_serving("id1", work_sessions=self.work, canon_sessions=self.canon)
        served = json.loads((self.canon / "2026-06-13_x" / "comparison_data.json").read_text(encoding="utf-8"))
        self.assertEqual(served["analysis"]["unified_summary"], "It compares X and Y.")
        self.assertEqual(len(served["analysis"]["topics"]), 1)

    def test_resolves_by_dir_name_too(self):
        _write_session(self.work, "2026-06-13_x", "id1", FULL)
        _write_session(self.canon, "2026-06-13_x", "id1", EMPTY)
        cs._promote_session_for_serving("2026-06-13_x", work_sessions=self.work, canon_sessions=self.canon)
        served = json.loads((self.canon / "2026-06-13_x" / "comparison_data.json").read_text(encoding="utf-8"))
        self.assertTrue(served["analysis"]["unified_summary"])

    def test_does_not_clobber_canonical_when_working_empty(self):
        # Re-launch from an env where the working copy is empty must NOT overwrite a good canonical.
        _write_session(self.work, "2026-06-13_x", "id1", EMPTY)
        _write_session(self.canon, "2026-06-13_x", "id1", FULL)
        cs._promote_session_for_serving("id1", work_sessions=self.work, canon_sessions=self.canon)
        served = json.loads((self.canon / "2026-06-13_x" / "comparison_data.json").read_text(encoding="utf-8"))
        self.assertEqual(served["analysis"]["unified_summary"], "It compares X and Y.")

    def test_noop_when_work_equals_canon(self):
        _write_session(self.work, "2026-06-13_x", "id1", FULL)
        # same dir for src and dst -> no-op, must not raise or duplicate
        cs._promote_session_for_serving("id1", work_sessions=self.work, canon_sessions=self.work)
        served = json.loads((self.work / "2026-06-13_x" / "comparison_data.json").read_text(encoding="utf-8"))
        self.assertTrue(served["analysis"]["unified_summary"])


if __name__ == "__main__":
    unittest.main()
