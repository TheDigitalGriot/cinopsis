"""F-A: the structural-check verdict of scripts/pre-release-audit.mjs.

Drives the real module (scripts/audit-structural-verdict.mjs) through node, so the test
exercises the code the gate runs rather than a Python re-statement of it.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

MODULE = (Path(__file__).resolve().parent.parent / "scripts" / "audit-structural-verdict.mjs").as_uri()
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(NODE is None, reason="node not on PATH")


def verdict(changed, scanned, failed_during=False):
    changed_js = "null" if changed is None else f"new Set({json.dumps(changed)})"
    src = (
        f"import {{ structuralVerdict }} from {json.dumps(MODULE)};"
        f"console.log(JSON.stringify(structuralVerdict({{ changed: {changed_js}, "
        f"scanned: {scanned}, failedDuring: {json.dumps(failed_during)} }})));"
    )
    r = subprocess.run([NODE, "--input-type=module", "-e", src], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def test_range_with_no_structural_files_passes_explicitly():
    v = verdict(["scripts/backfill_catchups.py", "tests/test_x.py", "CHANGELOG.md"], scanned=0)
    assert v["mark"] == "PASS"
    assert v["countsAsFailure"] is False
    assert v["message"] == "structural checks: 0 in-scope files (range touches no skills/commands/agents/hooks)"


def test_in_scope_files_but_none_examined_still_fails_zero_scan():
    v = verdict(["scripts/a.py", "skills/cinopsis/references/notes.txt"], scanned=0)
    assert v["mark"] == "FAIL"
    assert v["countsAsFailure"] is True
    assert "AUDIT_STRUCTURAL_ZERO_SCAN" in v["message"]


def test_normal_case_in_scope_and_examined_passes():
    v = verdict(["skills/cinopsis/SKILL.md", "scripts/a.py"], scanned=2)
    assert v["mark"] == "PASS"
    assert v["countsAsFailure"] is False
    assert "1 in-scope, 2 examined" in v["message"]


def test_normal_case_reports_fail_when_a_check_failed():
    v = verdict(["commands/digest.md"], scanned=1, failed_during=True)
    assert v["mark"] == "FAIL"
    assert v["countsAsFailure"] is False  # the failing check already counted itself


def test_no_range_stays_fail_closed():
    v = verdict(None, scanned=0)
    assert v["mark"] == "FAIL"
    assert v["countsAsFailure"] is True
    assert "AUDIT_STRUCTURAL_ZERO_SCAN" in v["message"]
