import json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"cerebro-os"))
from jobs.build_company_registry_activation import build_registry,build_activation_matrix
from jobs.verify_tenant_isolation import verify

class MultiEmpresaTests(unittest.TestCase):
    def test_registry_and_activation_matrix_are_multi_company(self):
        with tempfile.TemporaryDirectory() as td:
            cfg=Path(td)/"cfg.json"
            cfg.write_text(json.dumps([
                {"company_id":"aion","legal_name":"AION","environment":"LAB","version":"1","autonomy_profile":"AUTONOMOUS_VENTURE","enabled":True},
                {"company_id":"fenix","legal_name":"Fenix","environment":"LAB","version":"1","autonomy_profile":"FENIX_SENSITIVE","enabled":True}
            ]),encoding="utf-8")
            reg=build_registry(cfg); matrix=build_activation_matrix(cfg)
            self.assertEqual(reg["company_count"],2)
            self.assertEqual(reg["cross_company_default"],"DENY")
            self.assertEqual({x["company_id"] for x in reg["companies"]},{"aion","fenix"})
            self.assertTrue(all(not x["automatic_prod_activation_allowed"] for x in matrix["rows"]))
            self.assertTrue(all("TENANT-001" not in x["required_engines"] for x in matrix["rows"]))

    def test_duplicate_company_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            cfg=Path(td)/"cfg.json"
            cfg.write_text(json.dumps([{"company_id":"aion"},{"company_id":"aion"}]),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"unique"):
                build_registry(cfg)

    def test_tenant_verifier_detects_payload_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); d=root/"incidents"; d.mkdir()
            (d/"aion.json").write_text(json.dumps({"company_id":"fenix","incidents":[]}),encoding="utf-8")
            out=verify(root)
            self.assertEqual(out["status"],"BLOCKED")
            self.assertEqual(out["violation_count"],1)

    def test_tenant_verifier_green_for_isolated_payloads(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); d=root/"incidents"; d.mkdir()
            (d/"aion.json").write_text(json.dumps({"company_id":"aion","incidents":[{"company_id":"aion"}]}),encoding="utf-8")
            (d/"fenix.json").write_text(json.dumps({"company_id":"fenix","incidents":[{"company_id":"fenix"}]}),encoding="utf-8")
            out=verify(root)
            self.assertEqual(out["status"],"GREEN")
            self.assertEqual(out["violation_count"],0)

if __name__=="__main__": unittest.main()
