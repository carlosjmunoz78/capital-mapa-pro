import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cerebro-os"))

from governance.policy import PolicyRequest
from learning.continuous_improvement import ImprovementCandidate, ImprovementObjective
from learning.continuous_improvement_runtime import ContinuousImprovementRuntime
from learning.improvement_governed_executor import GovernedImprovementContext, GovernedImprovementExecutor
from quality.evaluation import EvaluationResult
from quality.tribunal import TribunalDecision, REQUIRED_GATES


def context(*, candidate_value=11.0, eval_score=1.0, risk="LOW", evidence_missing=None):
    objective = ImprovementObjective("aion","SEO-001","seo","leads",10.0,"MAXIMIZE","AUTONOMOUS_VENTURE","LAB","1.0.0")
    refs = tuple((k,f"e://{k}") for k in ("baseline","candidate","tests","evaluation","tribunal","rollback","backup","observability","cost","policy"))
    candidate = ImprovementCandidate(objective,"1.1.0",candidate_value,refs)
    evaluation = EvaluationResult("SEO-001",eval_score,0.8,("e://eval",),"aion","LAB","1.0.0")
    gates = {g: True for g in REQUIRED_GATES}
    evidence = {g: f"e://tribunal/{g}" for g in REQUIRED_GATES}
    tribunal = TribunalDecision("SEO-001",gates,"aion","LAB",evidence,"1.0.0")
    policy = PolicyRequest("aion","aion","LAB","promote",risk=risk)
    stages = {s:f"e://stage/{s}" for s in ContinuousImprovementRuntime("aion","AUTONOMOUS_VENTURE").cycle.stages()}
    if evidence_missing:
        stages.pop(evidence_missing,None)
    return GovernedImprovementContext(candidate,(evaluation,),tribunal,policy,stages)


class GovernedExecutorTests(unittest.TestCase):
    def test_happy_path_full_cycle_green(self):
        rt = ContinuousImprovementRuntime("aion","AUTONOMOUS_VENTURE")
        snap = rt.run_until_pause(GovernedImprovementExecutor(context()))
        self.assertEqual(snap.status,"GREEN")

    def test_failed_evaluation_retries_then_blocks(self):
        rt = ContinuousImprovementRuntime("aion","AUTONOMOUS_VENTURE",max_red_retries=2)
        snap = rt.run_until_pause(GovernedImprovementExecutor(context(eval_score=0.1)))
        self.assertEqual(snap.status,"BLOCKED")

    def test_old_vs_new_regression_blocks(self):
        rt = ContinuousImprovementRuntime("aion","AUTONOMOUS_VENTURE")
        snap = rt.run_until_pause(GovernedImprovementExecutor(context(candidate_value=9.0)))
        self.assertEqual(snap.status,"BLOCKED")

    def test_high_risk_policy_requests_human(self):
        rt = ContinuousImprovementRuntime("aion","AUTONOMOUS_VENTURE")
        snap = rt.run_until_pause(GovernedImprovementExecutor(context(risk="HIGH")))
        self.assertEqual(snap.status,"HUMAN_REQUIRED")

    def test_missing_stage_evidence_waits(self):
        rt = ContinuousImprovementRuntime("aion","AUTONOMOUS_VENTURE")
        snap = rt.run_until_pause(GovernedImprovementExecutor(context(evidence_missing="TEST")))
        self.assertEqual(snap.status,"WAITING")
        self.assertEqual(rt.next_stage(),"TEST")

if __name__ == "__main__":
    unittest.main()
