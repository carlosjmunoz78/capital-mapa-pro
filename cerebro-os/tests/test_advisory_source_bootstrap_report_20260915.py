import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "advisory" / "source_bootstrap_report_20260915.json"
LOCK = ROOT / "advisory" / "source_lock_20260915.json"


def test_bootstrap_report_matches_source_lock_hashes():
    report = json.loads(REPORT.read_text())
    lock = json.loads(LOCK.read_text())
    lock_by_domain = {x["domain"]: x for x in lock["sources"]}
    for row in report["domains"]:
        expected = lock_by_domain[row["domain"]]
        assert row["file"] == expected["file"]
        assert row["sha256"] == expected["sha256"]
        assert row["verification"] == "VERIFIED"
        assert expected["status"] == "BOUND"
        assert row["bytes"] == expected["bytes"]
        assert row["section_count"] == expected["heading_count"]


def test_bootstrap_totals_are_exact():
    report = json.loads(REPORT.read_text())
    verified = [x for x in report["domains"] if x["verification"] == "VERIFIED"]
    summary = report["summary"]
    assert len(verified) == 12
    assert sum(x["bytes"] for x in verified) == summary["verified_bytes"] == 1872321
    assert sum(x["line_count"] for x in verified) == summary["verified_lines"] == 78088
    assert sum(x["section_count"] for x in verified) == summary["verified_sections"] == 7410
    assert summary["missing_artifact"] == 0


def test_source_integrity_green_does_not_promote_knowledge_or_autonomy():
    report = json.loads(REPORT.read_text())
    promotion = report["promotion"]
    assert promotion["source_integrity_green"] is True
    assert promotion["knowledge_green"] is False
    assert promotion["capability_green"] is False
    assert promotion["autonomy_green"] is False
