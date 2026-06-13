import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import persist_session as ps


def _make_session(root, dir_name, sid, title, created_at):
    sdir = Path(root) / "sessions" / dir_name
    sdir.mkdir(parents=True, exist_ok=True)
    data = {"session": {"id": sid, "title": title, "created_at": created_at, "video_count": 1},
            "videos": [], "analysis": {}, "stats": {}}
    (sdir / "comparison_data.json").write_text(json.dumps(data), encoding="utf-8")
    idx = Path(root) / "sessions" / "index.json"
    cur = json.loads(idx.read_text(encoding="utf-8")) if idx.exists() else []
    cur.insert(0, {"id": sid, "title": title, "created_at": created_at,
                   "video_count": 1, "dir_name": dir_name})
    idx.write_text(json.dumps(cur), encoding="utf-8")


class TestPersistSession(unittest.TestCase):
    def setUp(self):
        self.src_sessions = Path(tempfile.mkdtemp()) / "sessions"
        self.dst_sessions = Path(tempfile.mkdtemp()) / "sessions"
        self.src_root = self.src_sessions.parent

    def test_copies_session_and_merges_index(self):
        _make_session(self.src_root, "2026-06-13_a", "id_a", "A", "2026-06-13T10:00:00")
        out = ps.persist_session("2026-06-13_a", self.src_sessions, self.dst_sessions)
        self.assertTrue((out / "comparison_data.json").exists())
        idx = json.loads((self.dst_sessions / "index.json").read_text(encoding="utf-8"))
        self.assertEqual([e["id"] for e in idx], ["id_a"])

    def test_noop_when_src_equals_dst(self):
        _make_session(self.src_root, "2026-06-13_a", "id_a", "A", "2026-06-13T10:00:00")
        self.assertIsNone(ps.persist_session("2026-06-13_a", self.src_sessions, self.src_sessions))

    def test_dedupe_by_id_and_newest_first(self):
        _make_session(self.src_root, "2026-06-13_a", "id_a", "A", "2026-06-13T10:00:00")
        _make_session(self.src_root, "2026-06-14_b", "id_b", "B", "2026-06-14T10:00:00")
        ps.persist_session("2026-06-13_a", self.src_sessions, self.dst_sessions)
        ps.persist_session("2026-06-14_b", self.src_sessions, self.dst_sessions)
        ps.persist_session("2026-06-13_a", self.src_sessions, self.dst_sessions)  # re-persist, same id
        idx = json.loads((self.dst_sessions / "index.json").read_text(encoding="utf-8"))
        self.assertEqual([e["id"] for e in idx], ["id_b", "id_a"])

    def test_index_written_without_bom(self):
        _make_session(self.src_root, "2026-06-13_a", "id_a", "A", "2026-06-13T10:00:00")
        ps.persist_session("2026-06-13_a", self.src_sessions, self.dst_sessions)
        raw = (self.dst_sessions / "index.json").read_bytes()
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
        json.loads(raw.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
