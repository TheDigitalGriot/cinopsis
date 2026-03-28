# tests/test_compare_videos.py
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from compare_videos import parse_urls, generate_session_id, build_session_dir_name


class TestParseUrls(unittest.TestCase):
    def test_full_urls(self):
        urls = ["https://www.youtube.com/watch?v=abc123def45", "https://youtu.be/xyz789ghi01"]
        result = parse_urls(urls)
        self.assertEqual(result, ["abc123def45", "xyz789ghi01"])

    def test_bare_ids(self):
        result = parse_urls(["abc123def45", "xyz789ghi01"])
        self.assertEqual(result, ["abc123def45", "xyz789ghi01"])

    def test_mixed(self):
        result = parse_urls(["https://www.youtube.com/watch?v=abc123def45", "xyz789ghi01"])
        self.assertEqual(result, ["abc123def45", "xyz789ghi01"])


class TestGenerateSessionId(unittest.TestCase):
    def test_returns_string(self):
        sid = generate_session_id()
        self.assertIsInstance(sid, str)
        self.assertGreater(len(sid), 8)


class TestBuildSessionDirName(unittest.TestCase):
    def test_format(self):
        name = build_session_dir_name("GPT-5 Announcements!")
        self.assertTrue(name.startswith("20"))
        self.assertIn("gpt-5-announcements", name)

    def test_sanitizes_special_chars(self):
        name = build_session_dir_name("What's New? (2026)")
        self.assertNotIn("?", name)
        self.assertNotIn("'", name)
        self.assertNotIn("(", name)


if __name__ == "__main__":
    unittest.main()
