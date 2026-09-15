import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "advisory" / "knowledge_validation_stage1_20260915.json"
LOCK = ROOT / "advisory" / "source_lock_20260915.json"


def test_stage1_covers_exactly_12_domains():
    data = json.loads(AUDIT.read_text())
    assert data["summary"]["domains"] == 12
    assert len(data["domains"]) == 12
    assert len({x["domain"] for x in data["domains"]}) == 12


def test_all_domains_structure_green():
    data = json.loads(AUDIT.read_text())
    assert data["summary"]["structure_green"] == 12
    for row in data["domains"]:
        assert row["structure_green"] is True
        assert all(row["checks"].values())
        assert len(row["sha256"]) == 64
        int(row["sha256"], 16)
        assert row["bytes"] > 0
        assert row["headings"] > 0


def test_stage1_hashes_match_canonical_source_lock():
    audit = json.loads(AUDIT.read_text())
    lock = json.loads(LOCK.read_text())
    locked = {x["domain"]: x for x in lock["sources"]}
    for row in audit["domains"]:
        assert row["file"] == locked[row["domain"]]["file"]
        assert row["sha256"] == locked[row["domain"]]["sha256"]
        assert row["bytes"] == locked[row["domain"]]["bytes"]


def test_structure_does_not_promote_knowledge_or_autonomy():
    data = json.loads(AUDIT.read_text())
    assert data["summary"]["knowledge_green"] == 0
    assert data["summary"]["capability_green"] is False
    assert data["summary"]["autonomy_green"] is False
    assert data["summary"]["prod_enabled"] is False
    assert all(row["knowledge_green"] is False for row in data["domains"])
