import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def load(name, rel):
    path=ROOT/rel; spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod
m=load("mortgage_engines_84_108","mortgage/engines.py")

class Loops84To108Tests(unittest.TestCase):
    def test_84_doc_extract(self):
        d=m.DocumentRecord("fenix","d1","DNI","h","src",.9,(("name","Ana"),)); self.assertEqual("GREEN",d.extraction_status)
    def test_85_doc_pending(self):
        d=m.DocumentRecord("fenix","d1","DNI","h","src",.9); self.assertEqual(("NOMINA",),m.pending_documents(("DNI","NOMINA"),(d,)))
    def test_86_doc_quality(self):
        d=m.DocumentRecord("fenix","d1","DNI","h","src",.9,(("name","Ana"),)); self.assertEqual("GREEN",m.document_quality(d,("name",))); self.assertEqual("RED",m.document_quality(d,("name","id")))
    def test_87_antifraud(self):
        a=m.DocumentRecord("f","a","X","same","s1",1); b=m.DocumentRecord("f","b","Y","same","s2",1); self.assertTrue(m.antifraud_signals((a,b)))
    def test_88_kyc(self):
        self.assertEqual(("GREEN",None),m.IdentityCheck("f","p","Ana","ana","1","1",.9).decision()); self.assertEqual("HUMAN_REQUIRED",m.IdentityCheck("f","p","Ana","Ana","1","2",.9).decision()[0])
    def test_89_aml(self):
        self.assertEqual(("GREEN",None),m.AmlAssessment(True,True,False,"e").decision()); self.assertEqual(("HUMAN_REQUIRED","LEGAL_REQUIRED"),m.AmlAssessment(True,False,False,"e").decision())
    def test_90_bank_knowledge(self):
        x=m.BankCriterion("b","ratio","x","src","2026-09-11T00:00:00+00:00",.9,3); x.validate()
    def test_91_bank_rank(self):
        opts=(m.BankOption("a",.8,.7,.5,"e"),m.BankOption("b",.7,.9,.5,"e")); self.assertEqual(("b","a"),m.rank_banks(opts,{"approval_fit":1,"price_score":2,"speed_score":1}))
    def test_92_routing(self):
        self.assertEqual(("RETRY","a"),m.RoutingDecision("a","x",True,0,3,("b",)).next_action()); self.assertEqual(("ROUTE_NEXT","b"),m.RoutingDecision("a","x",False,0,3,("b",)).next_action())
    def test_93_dossier(self):
        self.assertTrue(m.BankDossier("b",("d1",),"std","msg").ready)
    def test_94_followup(self):
        x=m.BankFollowUp("b","2026-09-10T00:00:00+00:00",24,"EMAIL"); self.assertTrue(x.due(datetime(2026,9,11,1,tzinfo=timezone.utc)))
    def test_95_negotiation(self):
        self.assertEqual(("GREEN",None),m.NegotiationProposal(.1,.2,"e").decision()); self.assertEqual("HUMAN_REQUIRED",m.NegotiationProposal(.3,.2,"e").decision()[0])
    def test_96_offer_compare(self):
        rows=(m.MortgageOffer("a",Decimal("100"),Decimal("2"),Decimal("1"),"e"),m.MortgageOffer("b",Decimal("90"),Decimal("3"),Decimal("1"),"e")); self.assertEqual(("b","a"),m.compare_offers(rows))
    def test_97_recommendation(self):
        self.assertEqual(("GREEN","a"),m.final_recommendation(("a",),.9,("r",))); self.assertEqual("HUMAN_REQUIRED",m.final_recommendation(("a",),.5,("r",))[0])
    def test_98_valuation(self):
        self.assertEqual("GREEN",m.ValuationEstimate(Decimal("100000"),.9,5,("e",)).status(10)); self.assertEqual("BLOCKED",m.ValuationEstimate(Decimal("100000"),.9,20,("e",)).status(10))
    def test_99_property_risk(self):
        self.assertEqual(("GREEN",None),m.PropertyRisk(False,False,False,("e",)).decision()); self.assertEqual(("HUMAN_REQUIRED","LEGAL_REQUIRED"),m.PropertyRisk(True,False,False,("e",)).decision())
    def test_100_registry(self):
        self.assertEqual("GREEN",m.RegistryExtract("Ana",(),(),(),"e",.9).status())
    def test_101_cadastre(self):
        c=m.CadastralExtract("ref",100,"residential","p","src"); c.validate(); self.assertTrue(m.registry_cadastre_coherent(100,102,3))
    def test_102_notary(self):
        self.assertEqual(("GREEN",None),m.NotaryReadiness(True,True,True,True,False).decision()); self.assertEqual(("HUMAN_REQUIRED","SIGNATURE_REQUIRED"),m.NotaryReadiness(True,True,True,True,True).decision())
    def test_103_payment(self):
        self.assertEqual(("GREEN",Decimal("0")),m.closing_balance(Decimal("100"),(Decimal("60"),Decimal("40"))))
    def test_104_sla(self):
        self.assertEqual("RED",m.SlaCase("2026-09-10T00:00:00+00:00").status(datetime(2026,9,11,tzinfo=timezone.utc)))
    def test_105_blocker(self):
        self.assertEqual("AUTO_RESOLVE",m.Blocker("b","LOW",True).action()); self.assertEqual("HUMAN_REQUIRED",m.Blocker("b","HIGH",False,"HIGH_RISK").action())
    def test_106_nba(self):
        self.assertEqual("a",m.next_best_action((m.ActionCandidate("a",10,2,1),m.ActionCandidate("b",5,1,0))))
    def test_107_agenda(self):
        c=(m.CalendarSlot("2026-09-11T10:00:00","2026-09-11T11:00:00"),m.CalendarSlot("2026-09-11T11:00:00","2026-09-11T12:00:00")); b=(m.CalendarSlot("2026-09-11T10:30:00","2026-09-11T11:00:00"),); self.assertEqual(c[1],m.first_free_slot(c,b))
    def test_108_third_party(self):
        t=m.ThirdPartyTask("bank","t1","2026-09-12T00:00:00+00:00","e"); self.assertEqual("GREEN",t.status(datetime(2026,9,11,tzinfo=timezone.utc)))

if __name__=="__main__": unittest.main()
