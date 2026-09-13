from pathlib import Path
import runpy


def test_security_lab_boundary_is_fail_closed_and_not_promoted():
    mod = runpy.run_path(str(Path(__file__).parents[1] / "runtime" / "security_lab_readonly_evidence_20260913.py"))
    result = mod["assess"]()
    assert result["fail_closed_lab_green"] is True
    assert result["real_business_replay_proven"] is False
    assert result["prod_parity_green"] is False
    assert result["prod_touched"] is False
    assert result["app_touched"] is False
    assert result["crm_touched"] is False
