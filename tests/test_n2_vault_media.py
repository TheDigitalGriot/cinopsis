"""N2 (2026-10-15): the vault holds the videos, not just the sessions.

persist_session copies every video's transcript_<id>.* and description_<id>.txt
into the vault data dir - additive, idempotent, never over a newer vault file -
and verify_invariants INV4 checks the vault is self-sufficient.
"""
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import persist_session as ps  # noqa: E402
import verify_invariants as vi  # noqa: E402

VID_A, VID_B, VID_C = "aaaaaaaaaaa", "bbbbbbbbbbb", "ccccccccccc"


def _session(root, dir_name, videos):
    sdir = Path(root) / "sessions" / dir_name
    sdir.mkdir(parents=True, exist_ok=True)
    data = {"session": {"id": dir_name, "title": dir_name, "created_at": "2026-10-15",
                        "video_count": len(videos)},
            "videos": videos, "analysis": {}, "stats": {}}
    (sdir / "comparison_data.json").write_text(json.dumps(data), encoding="utf-8")
    idx = Path(root) / "sessions" / "index.json"
    cur = json.loads(idx.read_text(encoding="utf-8")) if idx.exists() else []
    cur.append({"id": dir_name, "title": dir_name, "created_at": "2026-10-15",
                "video_count": len(videos), "dir_name": dir_name})
    idx.write_text(json.dumps(cur), encoding="utf-8")


class TestPromoteMedia(unittest.TestCase):
    def setUp(self):
        self.src = Path(tempfile.mkdtemp()) / "data"
        self.dst = Path(tempfile.mkdtemp()) / "vault"
        self.src.mkdir()
        (self.src / f"transcript_{VID_A}.json").write_text("[]", encoding="utf-8")
        (self.src / f"transcript_{VID_A}.txt").write_text("[00:00] hi", encoding="utf-8")
        (self.src / f"description_{VID_A}.txt").write_text("desc a", encoding="utf-8")
        (self.src / "_drip" / "desc").mkdir(parents=True)
        (self.src / "_drip" / "desc" / f"description_{VID_B}.txt").write_text("drip b", encoding="utf-8")
        _session(self.src, "2026-10-15_s", [{"id": VID_A, "title": "A"},
                                            {"id": VID_B, "title": "B"},
                                            {"id": VID_C, "title": "C"}])

    def _persist(self):
        report = ps.new_media_report()
        ps.persist_session("2026-10-15_s", self.src / "sessions", self.dst / "sessions",
                           media_report=report)
        return report

    def test_copies_transcripts_and_descriptions_same_layout(self):
        report = self._persist()
        for name in (f"transcript_{VID_A}.json", f"transcript_{VID_A}.txt",
                     f"description_{VID_A}.txt", f"_drip/desc/description_{VID_B}.txt"):
            self.assertTrue((self.dst / name).is_file(), name)
        self.assertEqual(report["transcripts_copied"], 2)
        self.assertEqual(report["descriptions_copied"], 2)

    def test_additive_source_untouched(self):
        self._persist()
        self.assertTrue((self.src / f"transcript_{VID_A}.json").is_file())
        self.assertEqual((self.src / f"description_{VID_A}.txt").read_text(encoding="utf-8"), "desc a")

    def test_missing_reported_per_id_not_fatal(self):
        report = self._persist()
        self.assertEqual(sorted(report["missing_transcript"]), [VID_B, VID_C])
        self.assertEqual(report["missing_description"], [VID_C])

    def test_idempotent(self):
        self._persist()
        again = self._persist()
        self.assertEqual(again["copied"] + again["refreshed"], 0)
        self.assertEqual(again["skipped"], 4)

    def test_newer_vault_file_not_overwritten(self):
        self._persist()
        vault_copy = self.dst / f"description_{VID_A}.txt"
        vault_copy.write_text("edited in vault", encoding="utf-8")
        future = time.time() + 60
        os.utime(vault_copy, (future, future))
        self._persist()
        self.assertEqual(vault_copy.read_text(encoding="utf-8"), "edited in vault")

    def test_older_vault_file_refreshed_from_newer_source(self):
        self._persist()
        vault_copy = self.dst / f"transcript_{VID_A}.txt"
        past = time.time() - 3600
        os.utime(vault_copy, (past, past))
        report = self._persist()
        self.assertEqual(report["refreshed"], 1)

    def test_backfill_covers_sessions_already_in_vault(self):
        _session(self.dst, "2026-10-15_s", [{"id": VID_A, "title": "A"}])
        report = ps.backfill_media(self.src, self.dst / "sessions")
        self.assertEqual(report["sessions"], 1)
        self.assertTrue((self.dst / f"transcript_{VID_A}.json").is_file())
        self.assertEqual(ps.backfill_media(self.src, self.dst / "sessions")["copied"], 0)

    def test_cli_backfill_flag(self):
        os.environ["CINOPSIS_DATA_DIR"] = str(self.dst)
        try:
            _session(self.dst, "2026-10-15_s", [{"id": VID_A, "title": "A"}])
            orig = ps.DATA_DIR
            ps.DATA_DIR = self.src
            try:
                self.assertEqual(ps.main(["--backfill-media"]), 0)
            finally:
                ps.DATA_DIR = orig
            self.assertTrue((self.dst / f"transcript_{VID_A}.txt").is_file())
        finally:
            del os.environ["CINOPSIS_DATA_DIR"]


class TestInv4VaultSelfSufficient(unittest.TestCase):
    def _store(self, videos, transcript_ids=()):
        root = Path(tempfile.mkdtemp()) / "vault"
        root.mkdir()
        _session(root, "2026-10-15_s", videos)
        for vid in transcript_ids:
            (root / f"transcript_{vid}.json").write_text("[]", encoding="utf-8")
        return vi.Store(root, canonical=True)

    def test_passes_when_every_video_has_vault_transcript(self):
        store = self._store([{"id": VID_A}], transcript_ids=[VID_A])
        violations, _ = vi.check_vault_self_sufficient([store])
        self.assertEqual(violations, [])

    def test_declared_non_transcript_source_exempt(self):
        store = self._store([{"id": VID_B, "digest_source": "description"},
                             {"id": "", "id_status": "unresolved"}])
        self.assertEqual(vi.check_vault_self_sufficient([store])[0], [])

    def test_fails_when_transcript_only_pooled_elsewhere(self):
        store = self._store([{"id": VID_A, "transcript": [{"text": "inline"}]}])
        violations, _ = vi.check_vault_self_sufficient([store])
        self.assertEqual(len(violations), 1)
        self.assertIn(VID_A, violations[0])

    def test_non_canonical_store_not_judged(self):
        store = self._store([{"id": VID_A}])
        store.canonical = False
        self.assertEqual(vi.check_vault_self_sufficient([store])[0], [])

    def test_self_test_still_fires(self):
        self.assertEqual(vi.self_test(), 0)


if __name__ == "__main__":
    unittest.main()
