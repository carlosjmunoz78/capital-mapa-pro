import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from advisory.tribunal import adjudicate


def test_tribunal_is_ready_for_knowledge_validation_with_12_sources():
    verdict = adjudicate(
        ROOT / "advisory" / "readiness_20260915.json",
        ROOT / "advisory" / "source_bootstrap_report_20260915.json",
    )
    assert verdict["architecture_green"] is True
    assert verdict["source_integrity_verified_domains"] == 12
    assert verdict["missing_domains"] == []
    assert verdict["ready_for_12_domain_tribunal"] is True
    assert verdict["verdict"] == "READY_FOR_KNOWLEDGE_VALIDATION"
    assert verdict["blocker"] is None


def test_tribunal_never_promotes_from_source_completeness_only():
    verdict = adjudicate(
        ROOT / "advisory" / "readiness_20260915.json",
        ROOT / "advisory" / "source_bootstrap_report_20260915.json",
    )
    assert verdict["knowledge_green"] is False
    assert verdict["capability_green"] is False
    assert verdict["autonomy_green"] is False
    assert verdict["prod_enabled"] is False
