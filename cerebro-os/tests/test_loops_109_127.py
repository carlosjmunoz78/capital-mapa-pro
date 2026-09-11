import importlib.util,sys,unittest
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(n,r):
 p=ROOT/r;s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
e=load('enterprise_engines_109_127','enterprise/engines.py')
class T(unittest.TestCase):
 def test_109_hr_core(self):
  x=e.EmployeeProfile('u','financial',True,frozenset({'mortgage'}),'ev');x.validate();self.assertTrue(x.active)
 def test_110_recruiting(self):
  rows=(e.Candidate('a',(('fit',.9),),'e'),e.Candidate('b',(('fit',.5),),'e'));self.assertEqual(('a','b'),e.rank_candidates(rows,{'fit':1}))
 def test_111_onboarding(self):
  x=e.EmployeeOnboarding();self.assertEqual('ACCOUNTS',x.next())
  with self.assertRaises(ValueError):x.complete('TRAINING','e:training')
  with self.assertRaises(ValueError):x.complete('ACCOUNTS')
  for s in e.ONBOARDING:x.complete(s,f'e:{s}')
  self.assertIsNone(x.next());self.assertEqual('e:ACCOUNTS',x.evidence['ACCOUNTS'])
 def test_112_skills(self):
  self.assertEqual(('GREEN',None),e.SkillCertification('u','x',9,8,False,'e').decision());self.assertEqual(('HUMAN_REQUIRED','HIGH_RISK'),e.SkillCertification('u','x',9,8,True,'e').decision())
 def test_113_performance(self):
  self.assertEqual(('COACH:u:sales',),e.coaching_actions((e.PerformanceSignal('u','sales',5,10,'e'),)))
 def test_114_workforce(self):
  c=(e.WorkforceCandidate('a',.2,.9,.8,.5,.1),e.WorkforceCandidate('b',.9,.3,.5,.9,.3));w={'load':1,'specialty_fit':1,'performance':1,'zone_fit':1,'risk':1};self.assertEqual('a',e.assign_case(c,w))
 def test_115_legal(self):
  self.assertEqual(('GREEN',None),e.LegalFinding('x','y','boe:1','2026-09-01',.9,False).decision());self.assertEqual(('HUMAN_REQUIRED','LEGAL_REQUIRED'),e.LegalFinding('x','y','boe:1','2026-09-01',.9,True).decision())
 def test_116_tax(self):
  self.assertEqual(Decimal('21.00'),e.calculate_tax(Decimal('100'),e.TaxRule('r','v1','aeat:1',Decimal('.21'))))
 def test_117_compliance(self):
  self.assertEqual('GREEN',e.compliance_status((e.ComplianceControl('c',True,True,'e'),)));self.assertEqual('HUMAN_REQUIRED',e.compliance_status((e.ComplianceControl('c',True,False,'e'),)))
 def test_118_dpo(self):
  self.assertEqual(('BLOCKED',None),e.PrivacyRequest('READ',True,True,False).decision())
  self.assertEqual(('GREEN',None),e.PrivacyRequest('READ',True,True,False,'id:e','law:e').decision())
  self.assertEqual(('HUMAN_REQUIRED','LEGAL_REQUIRED'),e.PrivacyRequest('DELETE',True,True,False,'id:e','law:e').decision())
  self.assertEqual(('BLOCKED',None),e.PrivacyRequest('READ',False,True,False,'id:e','law:e').decision())
 def test_119_consent(self):
  self.assertEqual(('HUMAN_REQUIRED','SIGNATURE_REQUIRED'),e.ConsentDocument('d',True,True,False,False,True).status())
  self.assertEqual(('RED',None),e.ConsentDocument('d',True,True,True,True,True).status())
  self.assertEqual(('GREEN',None),e.ConsentDocument('d',True,True,True,True,True,'gen:e','sent:e','signed:e','arch:e').status())
 def test_120_invoice(self):
  x=e.Invoice('i','case',Decimal('100'),Decimal('21'),Decimal('50'),'e');self.assertEqual(Decimal('121'),x.total);self.assertEqual(Decimal('71'),x.balance);self.assertEqual('GREEN',x.status())
 def test_121_receivables(self):
  x=e.Receivable('i','2026-09-10T00:00:00+00:00',Decimal('10'),1);self.assertEqual('REMIND',x.action(datetime(2026,9,11,tzinfo=timezone.utc)))
 def test_122_treasury(self):
  x=e.CashFlow(Decimal('100'),Decimal('50'),Decimal('20'),Decimal('10'));self.assertEqual(Decimal('120'),x.forecast);self.assertEqual('GREEN',x.status(Decimal('50')))
 def test_123_accounting(self):
  self.assertEqual(('GREEN',()),e.accounting_package((e.AccountingItem('d','expense',Decimal('10'),True),)))
 def test_124_vendor(self):
  self.assertEqual('GREEN',e.VendorHealth('v',True,.2,'2027-01-01',True,'e').status());self.assertEqual('HUMAN_REQUIRED',e.VendorHealth('v',False,.2,'2027-01-01',True,'e').status())
 def test_125_procurement(self):
  rows=(e.ProcurementOption('a',Decimal('10'),Decimal('30'),.1,'e'),e.ProcurementOption('b',Decimal('20'),Decimal('25'),.1,'e'));self.assertEqual(('GREEN','a'),e.procurement_decision(rows,Decimal('20')));self.assertEqual(('HUMAN_REQUIRED','MONEY_LIMIT'),e.procurement_decision(rows,Decimal('5')))
 def test_126_vendor_replace(self):
  self.assertEqual(('GREEN',None),e.VendorReplacement('a','b',True,True,False,'e').decision());self.assertEqual(('HUMAN_REQUIRED','HIGH_RISK'),e.VendorReplacement('a','b',True,True,True,'e').decision())
 def test_127_vendor_contract(self):
  x=e.VendorContract('v','2026-09-20T00:00:00+00:00','2026-12-01T00:00:00+00:00',True,'e');self.assertEqual('REVIEW_RENEWAL',x.action(datetime(2026,9,11,tzinfo=timezone.utc),30))
if __name__=='__main__':unittest.main()
