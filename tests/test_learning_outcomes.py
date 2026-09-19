import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))

from jobs.derive_learning_outcomes import run


def write_audit(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    conn=sqlite3.connect(path)
    conn.execute("""CREATE TABLE improvement_audit(
      seq INTEGER PRIMARY KEY AUTOINCREMENT,
      company_id TEXT NOT NULL,
      environment TEXT NOT NULL,
      cycle_id TEXT NOT NULL,
      payload_json TEXT NOT NULL,
      previous_hash TEXT NOT NULL,
      record_hash TEXT NOT NULL UNIQUE
    )""")
    for i,row in enumerate(rows,1):
        payload=json.dumps(row,sort_keys=True)
        conn.execute(
            "INSERT INTO improvement_audit(company_id,environment,cycle_id,payload_json,previous_hash,record_hash) VALUES(?,?,?,?,?,?)",
            (row["company_id"],row["environment"],row["cycle_id"],payload,"GENESIS" if i==1 else f"h{i-1}",f"h{i}")
        )
    conn.commit(); conn.close()


class LearningOutcomeTests(unittest.TestCase):
    def _cfg(self, root: Path):
        cfg=root/"companies.json"
        cfg.write_text(json.dumps([{
            "company_id":"aion","legal_name":"AION","autonomy_profile":"AUTONOMOUS_VENTURE",
            "environment":"LAB","version":"1.0.0","interval_hours":24,"enabled":True
        }]),encoding="utf-8")
        return cfg

    def test_regression_creates_candidate_only_rule(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); cfg=self._cfg(root)
            audit=root/"state"/"state"/"aion"/"LAB"/"1.0.0"/"audit.db"
            write_audit(audit,[
                {"company_id":"aion","engine_id":"SUP-001","environment":"LAB","version":"1.0.0","cycle_id":"c1","stage":"TEST","status":"GREEN","evidence_ref":"e://1"},
                {"company_id":"aion","engine_id":"SUP-001","environment":"LAB","version":"1.0.0","cycle_id":"c2","stage":"TEST","status":"BLOCKED","evidence_ref":"e://2"},
            ])
            old=os.environ.copy()
            os.environ["CEREBRO_IMPROVEMENT_STATE_ROOT"]=str(root/"state")
            os.environ["CEREBRO_IMPROVEMENT_COMPANIES"]=str(cfg)
            os.environ["CEREBRO_LEARNING_OUTCOME_ROOT"]=str(root/"out")
            try: run()
            finally: os.environ.clear(); os.environ.update(old)
            p=json.loads((root/"out"/"aion.json").read_text())
            self.assertEqual(p["cycles_observed"],2)
            self.assertEqual(p["comparisons"][0]["trend"],"REGRESSED")
            c=p["rule_candidates"][0]
            self.assertEqual(c["engine_id"],"LRN-001")
            self.assertEqual(c["status"],"CANDIDATE_ONLY")
            self.assertFalse(c["auto_promote_allowed"])
            self.assertFalse(c["policy_change_allowed"])
            self.assertFalse(c["threshold_reduction_allowed"])
            self.assertFalse(c["external_mutation_allowed"])

    def test_improvement_is_recorded_but_not_auto_promoted(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); cfg=self._cfg(root)
            audit=root/"state"/"state"/"aion"/"LAB"/"1.0.0"/"audit.db"
            write_audit(audit,[
                {"company_id":"aion","engine_id":"SUP-001","environment":"LAB","version":"1.0.0","cycle_id":"c1","stage":"TEST","status":"BLOCKED","evidence_ref":"e://1"},
                {"company_id":"aion","engine_id":"SUP-001","environment":"LAB","version":"1.0.0","cycle_id":"c2","stage":"TEST","status":"GREEN","evidence_ref":"e://2"},
            ])
            old=os.environ.copy()
            os.environ["CEREBRO_IMPROVEMENT_STATE_ROOT"]=str(root/"state")
            os.environ["CEREBRO_IMPROVEMENT_COMPANIES"]=str(cfg)
            os.environ["CEREBRO_LEARNING_OUTCOME_ROOT"]=str(root/"out")
            try: run()
            finally: os.environ.clear(); os.environ.update(old)
            p=json.loads((root/"out"/"aion.json").read_text())
            self.assertEqual(p["comparisons"][0]["trend"],"IMPROVED")
            self.assertEqual(p["rule_candidates"][0]["candidate_action"],"PRESERVE_SUCCESSFUL_PATTERN")
            self.assertFalse(p["rule_candidates"][0]["auto_promote_allowed"])

    def test_single_cycle_does_not_invent_learning(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); cfg=self._cfg(root)
            audit=root/"state"/"state"/"aion"/"LAB"/"1.0.0"/"audit.db"
            write_audit(audit,[
                {"company_id":"aion","engine_id":"SUP-001","environment":"LAB","version":"1.0.0","cycle_id":"c1","stage":"TEST","status":"GREEN","evidence_ref":"e://1"},
            ])
            old=os.environ.copy()
            os.environ["CEREBRO_IMPROVEMENT_STATE_ROOT"]=str(root/"state")
            os.environ["CEREBRO_IMPROVEMENT_COMPANIES"]=str(cfg)
            os.environ["CEREBRO_LEARNING_OUTCOME_ROOT"]=str(root/"out")
            try: run()
            finally: os.environ.clear(); os.environ.update(old)
            p=json.loads((root/"out"/"aion.json").read_text())
            self.assertEqual(p["rule_candidates"],[])
            self.assertEqual(p["status"],"INSUFFICIENT_OR_STABLE_EVIDENCE")


if __name__=="__main__":
    unittest.main()
