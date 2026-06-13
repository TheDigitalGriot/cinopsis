import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import compare_server


class TestServerDataDir(unittest.TestCase):
    def test_reads_sessions_from_explicit_data_dir(self):
        tmp = tempfile.mkdtemp()
        sessions = Path(tmp) / "sessions"
        sessions.mkdir(parents=True)
        (sessions / "index.json").write_text(json.dumps(
            [{"id": "x", "title": "T", "created_at": "2026-06-13T00:00:00",
              "video_count": 1, "dir_name": "d"}]), encoding="utf-8")
        app = compare_server.create_app(data_dir=tmp)
        client = app.test_client()
        r = client.get("/api/sessions")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()[0]["id"], "x")


if __name__ == "__main__":
    unittest.main()
