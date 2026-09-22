import importlib.util,pathlib,sys,unittest
P=pathlib.Path(__file__).resolve().parents[1]/"identity"/"browser_operator_v16_protocol.py";S=importlib.util.spec_from_file_location("p",P);M=importlib.util.module_from_spec(S);sys.modules[S.name]=M;S.loader.exec_module(M)
class ProtocolTests(unittest.TestCase):
 def cmd(self,**kw):
  d=dict(command_id="x",company_id="fenix",environment="LAB",version="v0",action="OPERATOR_CLICK",target_url="http://127.0.0.1:8765/lab/operator-fixture",selector="#cerebro-button",value="");d.update(kw);return M.OperatorCommand(**d)
 def test_click_green(self):self.assertEqual(M.validate(self.cmd(),8765)["status"],"GREEN")
 def test_exact_target_only(self):
  for u in ("https://example.com/","http://127.0.0.1:8765/lab/operator-fixture?x=1","http://localhost:8765/lab/operator-fixture"):
   self.assertEqual(M.validate(self.cmd(target_url=u),8765)["status"],"BLOCKED")
 def test_action_selector_pairs(self):
  self.assertEqual(M.validate(self.cmd(action="OPERATOR_TYPE",selector="#cerebro-button",value="x"),8765)["status"],"BLOCKED")
  self.assertEqual(M.validate(self.cmd(action="OPERATOR_TYPE",selector="#cerebro-input",value="x"*65),8765)["status"],"BLOCKED")
 def test_receipts_semantic(self):
  self.assertTrue(M.verify_receipt("OPERATOR_CLICK","COMPLETED","LAB_OPERATOR_FIXTURE_VERIFIED","CLICKED"))
  self.assertFalse(M.verify_receipt("OPERATOR_CLICK","COMPLETED","LAB_OPERATOR_FIXTURE_VERIFIED","READY"))
  self.assertFalse(M.verify_receipt("OPERATOR_TYPE","FAILED","LAB_OPERATOR_FIXTURE_VERIFIED","x"))
 def test_no_prod_or_mutation(self):
  d=M.validate(self.cmd(),8765);self.assertFalse(d["external_mutation_allowed"]);self.assertFalse(d["prod_activation_allowed"]);self.assertFalse(d["secret_value_allowed"])
if __name__=="__main__":unittest.main()
