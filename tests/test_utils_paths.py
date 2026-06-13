import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _utils


class TestCanonicalDataDir(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("CINOPSIS_DATA_DIR", None)

    def test_default_path_shape(self):
        os.environ.pop("CINOPSIS_DATA_DIR", None)
        p = _utils.canonical_data_dir()
        self.assertEqual(p.name, "cinopsis-cinopsis")
        self.assertEqual(p.parent.name, "data")
        self.assertEqual(p.parent.parent.name, "plugins")

    def test_env_override(self):
        os.environ["CINOPSIS_DATA_DIR"] = os.path.join(os.sep, "tmp", "custom-cino")
        self.assertEqual(_utils.canonical_data_dir(), Path(os.sep) / "tmp" / "custom-cino")


if __name__ == "__main__":
    unittest.main()
