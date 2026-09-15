import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from advisory.source_integrity import all_bound_sources_verified, verify_source_directory

LOCK = ROOT / "advisory" / "source_lock_20260915.json"


def test_source_lock_has_11_bound_and_one_missing():
    data = json.loads(LOCK.read_text())
    assert data["summary"] == {"domains": 12, "bound": 11, "missing_artifact": 1, "historical_preserved": 1}
    assert sum(x["status"] == "BOUND" for x in data["sources"]) == 11
    legal = next(x for x in data["sources"] if x["domain"] == "JURIDICA_GENERAL")
    assert legal["status"] == "MISSING_ARTIFACT"
    assert legal["sha256"] is None


def test_every_bound_source_has_real_sha_and_size():
    data = json.loads(LOCK.read_text())
    for item in data["sources"]:
        if item["status"] != "BOUND":
            continue
        assert isinstance(item["bytes"], int) and item["bytes"] > 0
        assert isinstance(item["heading_count"], int) and item["heading_count"] > 0
        assert len(item["sha256"]) == 64
        int(item["sha256"], 16)


def test_historical_laboral_v01_is_preserved_not_canonical():
    data = json.loads(LOCK.read_text())
    old = data["historical_sources"][0]
    assert old["domain"] == "LABORAL"
    assert old["status"] == "SUPERSEDED_PRESERVED"
    current = next(x for x in data["sources"] if x["domain"] == "LABORAL")
    assert current["file"].endswith("v1.0_FINAL.md")


def test_verifier_fails_closed_when_physical_sources_absent(tmp_path):
    results = verify_source_directory(tmp_path, LOCK)
    assert results["JURIDICA_GENERAL"] == "MISSING_ARTIFACT"
    assert sum(v == "VERIFIED" for v in results.values()) == 0
    assert all_bound_sources_verified(results) is False
