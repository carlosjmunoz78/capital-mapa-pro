import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/"preprod"/"run_candidate.py"

spec=importlib.util.spec_from_file_location("cerebro_preprod_candidate_container",MODULE)
mod=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

class PreprodPersistentCandidateContractTests(unittest.TestCase):
    def test_remote_rehearsal_validation_targets_container_test_suite(self):
        calls=[]
        with patch.object(mod,"run_test_discovery",side_effect=lambda pattern,reason:calls.append((pattern,reason))):
            mod.run_remote_onboarding_rehearsal_validation()
        self.assertEqual(calls[0][0],"test_remote_company_e2e_rehearsal_v0.py")
        self.assertIn("remote onboarding E2E",calls[0][1])

    def test_persistent_candidate_runs_remote_rehearsal_before_server(self):
        order=[]
        with patch.object(mod,"run_persistent_representative_validation",side_effect=lambda:order.append("representative")),              patch.object(mod,"run_remote_onboarding_rehearsal_validation",side_effect=lambda:order.append("remote")),              patch.object(mod,"emit_persistent_observability_probe",side_effect=lambda:order.append("observability")),              patch.object(mod.ThreadingHTTPServer,"__init__",return_value=None),              patch.object(mod.ThreadingHTTPServer,"serve_forever",side_effect=RuntimeError("stop")):
            with self.assertRaisesRegex(RuntimeError,"stop"):
                mod.run_persistent_candidate()
        self.assertEqual(order[:3],["representative","remote","observability"])

if __name__=="__main__":
    unittest.main()
