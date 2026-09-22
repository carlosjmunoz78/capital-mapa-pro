import importlib.util, pathlib, sys, unittest
P=pathlib.Path(__file__).resolve().parents[1]/"identity"/"browser_operator_action_contract_v0.py"
S=importlib.util.spec_from_file_location("browser_operator",P); M=importlib.util.module_from_spec(S);sys.modules[S.name]=M;S.loader.exec_module(M)

class BrowserOperatorContractTests(unittest.TestCase):
    def req(self, action="NAVIGATE", **kw):
        x=dict(company_id="fenix",environment="LAB",version="v0",action=action,
               origin_allowlisted=True,connector_available=False,policy_green=True,
               session_authorized=True,rollback_available=True,confidence=.99)
        x.update(kw); return M.BrowserActionRequest(**x)
    def test_verified_navigation_contract_can_allow(self):
        d=M.decide_browser_action(self.req()); self.assertEqual(d["decision"],"ALLOW"); self.assertTrue(d["runtime_implemented"])
    def test_write_contract_exists_but_runtime_fails_closed(self):
        for a in ("CLICK","TYPE","UPLOAD","DOWNLOAD","SAVE_DRAFT","SUBMIT_FORM","PUBLISH","SEND_MESSAGE"):
            with self.subTest(a=a):
                d=M.decide_browser_action(self.req(a)); self.assertEqual(d["decision"],"BLOCK")
                self.assertIn("RUNTIME_ACTION_NOT_IMPLEMENTED",d["blockers"]); self.assertFalse(d["external_mutation_allowed"])
    def test_connector_first_and_rollback(self):
        d=M.decide_browser_action(self.req("SUBMIT_FORM",connector_available=True,rollback_available=False))
        self.assertIn("CONNECTOR_FIRST",d["blockers"]); self.assertIn("ROLLBACK_REQUIRED",d["blockers"])
    def test_canonical_human_exceptions(self):
        cases=[("CONFIRM_PAYMENT",dict(involves_money=True),"MONEY_LIMIT"),
               ("SIGN_LEGAL",dict(involves_legal_signature=True),"SIGNATURE_REQUIRED"),
               ("TYPE",dict(confidence=.4),"LOW_CONFIDENCE"),
               ("CLICK",dict(security_incident=True),"SECURITY_INCIDENT"),
               ("CLICK",dict(customer_requested_human=True),"CUSTOMER_HUMAN_REQUEST")]
        for a,kw,reason in cases:
            with self.subTest(a=a):
                d=M.decide_browser_action(self.req(a,**kw));self.assertEqual(d["decision"],"HUMAN_REQUIRED");self.assertEqual(d["human_reason"],reason)
    def test_prod_and_unlisted_origin_block(self):
        d=M.decide_browser_action(self.req(environment="PROD",origin_allowlisted=False))
        self.assertEqual(d["decision"],"BLOCK");self.assertIn("LAB_SCOPE_REQUIRED",d["blockers"]);self.assertIn("ORIGIN_NOT_ALLOWLISTED",d["blockers"])
if __name__=="__main__": unittest.main()
