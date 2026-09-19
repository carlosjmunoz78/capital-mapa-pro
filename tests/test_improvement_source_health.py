import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))

from observability.improvement_source_health import read_company_source_health, fleet_source_health
from console.improvement_status import export_console_source_status


class ImprovementSourceHealthTests(unittest.TestCase):
    def test_required_failure_is_waiting_and_visible_in_console(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"fenix.observations.json").write_text(json.dumps({
                "company_id":"fenix",
                "status":"SOURCE_ERROR",
                "evidence_ref":"e://web-error",
                "facts":{
                    "missing_required_sources":[],
                    "failed_required_sources":["business"],
                    "failed_optional_sources":["content"],
                    "source_status":{
                        "technical":{"status":"NO_CHANGE"},
                        "business":{"status":"SOURCE_ERROR"},
                        "content":{"status":"SOURCE_ERROR"}
                    }
                }
            }),encoding="utf-8")
            item=read_company_source_health(root,"fenix")
            self.assertEqual(item.status,"WAITING")
            self.assertEqual(item.required_failures,("business",))
            self.assertEqual(item.optional_failures,("content",))
            console=export_console_source_status(root,({"company_id":"fenix"},))
            self.assertEqual(console["status"],"WAITING")
            self.assertEqual(console["attention_company_ids"],("fenix",))

    def test_no_change_maps_to_green(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"aion.observations.json").write_text(json.dumps({
                "company_id":"aion","status":"NO_CHANGE","evidence_ref":"e://ok",
                "facts":{
                    "missing_required_sources":[],
                    "failed_required_sources":[],
                    "failed_optional_sources":[],
                    "source_status":{"technical":{"status":"NO_CHANGE"}}
                }
            }),encoding="utf-8")
            item=read_company_source_health(root,"aion")
            self.assertEqual(item.status,"GREEN")
            fleet=fleet_source_health(root,("aion",))
            self.assertEqual(fleet["status"],"GREEN")

    def test_proposal_ready_is_attention_not_failure(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"fenix.observations.json").write_text(json.dumps({
                "company_id":"fenix","status":"PROPOSAL_READY","evidence_ref":"e://proposal",
                "facts":{
                    "missing_required_sources":[],
                    "failed_required_sources":[],
                    "failed_optional_sources":[],
                    "source_status":{"technical":{"status":"NO_CHANGE"},"business":{"status":"PROPOSAL_READY"}}
                }
            }),encoding="utf-8")
            fleet=fleet_source_health(root,("fenix",))
            self.assertEqual(fleet["status"],"PROPOSAL_READY")
            self.assertEqual(fleet["attention_company_ids"],("fenix",))

    def test_cross_company_evidence_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"fenix.observations.json").write_text(json.dumps({
                "company_id":"other","status":"NO_CHANGE","evidence_ref":"e://x","facts":{}
            }),encoding="utf-8")
            with self.assertRaises(ValueError):
                read_company_source_health(root,"fenix")


if __name__=="__main__": unittest.main()
