# tests/test_session_persistence.py
import json
import os
import tempfile
import unittest
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import compare_videos


class TestSessionPersistence(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        compare_videos.SESSIONS_DIR = Path(self.tmpdir) / "sessions"
        os.environ["CINOPSIS_NO_PERSIST"] = "1"  # don't touch the real home dir

    def tearDown(self):
        os.environ.pop("CINOPSIS_NO_PERSIST", None)

    def test_save_session_creates_files(self):
        data = {
            "session": {"id": "test123", "title": "Test Session",
                        "created_at": "2026-03-28T14:00:00", "video_count": 2},
            "videos": [],
            "analysis": {"unified_summary": "", "topics": [], "disagreements": [], "key_moments": []},
            "stats": {"total_videos": 2, "common_topics": 0, "disagreements": 0, "key_moments": 0},
        }
        output_path = compare_videos.save_session(data)
        self.assertTrue(output_path.exists())
        index_path = Path(self.tmpdir) / "sessions" / "index.json"
        self.assertTrue(index_path.exists())
        with open(index_path) as f:
            index = json.load(f)
        self.assertEqual(len(index), 1)
        self.assertEqual(index[0]["id"], "test123")

    def test_index_prepends_new_sessions(self):
        for i, title in enumerate(["First", "Second"]):
            data = {
                "session": {"id": f"sess{i}", "title": title,
                            "created_at": "2026-03-28T14:00:00", "video_count": 1},
                "videos": [],
                "analysis": {"unified_summary": "", "topics": [], "disagreements": [], "key_moments": []},
                "stats": {"total_videos": 1, "common_topics": 0, "disagreements": 0, "key_moments": 0},
            }
            compare_videos.save_session(data)
        index_path = Path(self.tmpdir) / "sessions" / "index.json"
        with open(index_path) as f:
            index = json.load(f)
        self.assertEqual(len(index), 2)
        self.assertEqual(index[0]["title"], "Second")

    def test_save_session_persists_to_canonical(self):
        canon = Path(self.tmpdir) / "canonical" / "sessions"
        compare_videos.CANONICAL_SESSIONS_DIR = canon
        os.environ.pop("CINOPSIS_NO_PERSIST", None)
        title = "Persist Me"
        data = {
            "session": {"id": "persist1", "title": title,
                        "created_at": "2026-06-13T10:00:00", "video_count": 1},
            "videos": [],
            "analysis": {"unified_summary": "", "topics": [], "disagreements": [], "key_moments": []},
            "stats": {"total_videos": 1, "common_topics": 0, "disagreements": 0, "key_moments": 0},
        }
        compare_videos.save_session(data)
        dir_name = compare_videos.build_session_dir_name(title)
        self.assertTrue((canon / dir_name / "comparison_data.json").exists())
        idx = json.loads((canon / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(idx[0]["id"], "persist1")


if __name__ == "__main__":
    unittest.main()
