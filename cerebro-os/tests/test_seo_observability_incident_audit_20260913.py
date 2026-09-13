import importlib.util
from pathlib import Path

MODULE = Path(__file__).parents[1] / "runtime" / "seo_observability_incident_audit_20260913.py"
spec = importlib.util.spec_from_file_location("seo_obs_incident", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_retained_health_is_green_but_incident_path_stays_fail_closed():
    result = mod.assess()
    assert result["scenario_count"] == 2
    assert result["retained_success_runs"] == 5
    assert result["retained_error_runs"] == 0
    assert result["incomplete_executions"] == 0
    assert result["all_connections_ok"] is True
    assert result["retained_health_evidence_green"] is True
    assert result["incident_capture_path_proven"] is False
    assert result["seo_incident_observability_green"] is False
    assert result["scenario_mutation_performed"] is False
