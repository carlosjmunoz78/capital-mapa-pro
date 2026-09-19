import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cerebro-os"))

from learning.meta_learning import analyze
from jobs.analyze_meta_learning import run

def rec(cycle, stage, status, company="aion", environment="LAB", version="1.0.0", cost=0.0):
    return {
        "company_id": company,
        "environment": environment,
        "version": version,
        "cycle_id": cycle,
        "stage": stage,
        "status": status,
        "cost_eur": cost,
    }

class MetaLearningTests(unittest.TestCase):
    def test_requires_multiple_cycles_before_meta_change(self):
        s = analyze(
            [rec("c1", "EVALUATE", "WAITING")],
            company_id="aion", environment="LAB", version="1.0.0",
        )
        self.assertEqual(s.decision, "MORE_EVIDENCE")
        self.assertFalse(s.auto_apply_allowed)

    def test_detects_repeated_bottleneck_without_weakening_gates(self):
        records = [
            rec("c1", "EVALUATE", "WAITING"),
            rec("c2", "EVALUATE", "BLOCKED"),
            rec("c3", "EVALUATE", "WAITING"),
            rec("c1", "PROPOSE", "GREEN"),
            rec("c2", "PROPOSE", "GREEN"),
            rec("c3", "PROPOSE", "GREEN"),
        ]
        s = analyze(records, company_id="aion", environment="LAB", version="1.0.0")
        self.assertEqual(s.decision, "PROPOSE_META_EXPERIMENT")
        self.assertEqual(s.bottleneck_stage, "EVALUATE")
        self.assertFalse(s.anti_gaming["judge_modification_allowed"])
        self.assertFalse(s.anti_gaming["policy_weakening_allowed"])
        self.assertFalse(s.auto_apply_allowed)

    def test_scopes_company_environment_version(self):
        records = [
            rec("c1", "TEST", "BLOCKED", company="fenix"),
            rec("c2", "TEST", "BLOCKED", environment="PROD"),
            rec("c3", "TEST", "BLOCKED", version="2.0.0"),
            rec("a1", "TEST", "GREEN"),
            rec("a2", "TEST", "GREEN"),
            rec("a3", "TEST", "GREEN"),
        ]
        s = analyze(records, company_id="aion", environment="LAB", version="1.0.0")
        self.assertEqual(s.decision, "NO_CHANGE")
        self.assertIsNone(s.bottleneck_stage)

    def test_job_reads_append_only_audit_and_writes_non_mutating_record(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state_root = root / "improvement"
            cfg = root / "companies.json"
            meta_root = root / "meta"
            cfg.write_text(json.dumps([{
                "company_id":"aion","legal_name":"AION","autonomy_profile":"AUTONOMOUS_VENTURE",
                "environment":"LAB","version":"1.0.0","interval_hours":24,"enabled":True
            }]), encoding="utf-8")
            db = state_root / "state" / "aion" / "LAB" / "1.0.0" / "audit.db"
            db.parent.mkdir(parents=True)
            conn = sqlite3.connect(db)
            conn.execute("CREATE TABLE improvement_audit(seq INTEGER PRIMARY KEY AUTOINCREMENT,payload_json TEXT NOT NULL)")
            for cycle in ("c1","c2","c3"):
                conn.execute("INSERT INTO improvement_audit(payload_json) VALUES(?)", (
                    json.dumps(rec(cycle, "TEST", "WAITING")),
                ))
            conn.commit()
            conn.close()

            old = os.environ.copy()
            os.environ["CEREBRO_IMPROVEMENT_STATE_ROOT"] = str(state_root)
            os.environ["CEREBRO_IMPROVEMENT_COMPANIES"] = str(cfg)
            os.environ["CEREBRO_META_LEARNING_ROOT"] = str(meta_root)
            try:
                run()
            finally:
                os.environ.clear()
                os.environ.update(old)

            payload = json.loads((meta_root / "aion.json").read_text())
            self.assertEqual(payload["record_type"], "meta_learning_record")
            self.assertEqual(payload["decision"], "PROPOSE_META_EXPERIMENT")
            self.assertFalse(payload["external_mutation_allowed"])
            self.assertFalse(payload["production_ready"])
            self.assertFalse(payload["auto_apply_allowed"])

if __name__ == "__main__":
    unittest.main()
