import importlib.util,sys,unittest
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(n,r):
 p=ROOT/r;s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
x=load('multicompany_engines_164_185','multicompany/engines.py')
class T(unittest.TestCase):
 def test_164_company_registry(self):
  m=x.CompanyManifest('c','Co',('co.es',),'finance','ES','u',('LAB','PREPROD'),('FACT-001',));m.validate()
 def test_165_company_onboarding(self):
  o=x.CompanyOnboarding('c',environment='LAB',version='2.0.0');self.assertEqual('SCAN',o.next())
  with self.assertRaises(ValueError):o.update('SEO','GREEN')
  for p in x.ONBOARDING_PHASES:o.update(p,'GREEN')
  self.assertIsNone(o.next())
  with self.assertRaises(ValueError):x.CompanyOnboarding('c',environment='DEV')
 def test_166_scanner(self):x.FootprintFinding('WEB','https://x','src','2026-09-11',.9).validate()
 def test_167_keywords(self):
  r=(x.KeywordIdea('a','buy','ES',.9,None,'e'),x.KeywordIdea('b','info','ES',.3,None,'e'));self.assertEqual(('a','b'),x.rank_keywords(r))
 def test_168_web_audit(self):
  score,backlog=x.web_audit_score((x.WebAuditCheck('a',True,2,'e'),x.WebAuditCheck('b',False,1,'e')));self.assertEqual(.666667,score);self.assertEqual(('b',),backlog)
 def test_169_social_audit(self):x.SocialProfile('IG','ig:x',10,.1,'e').validate()
 def test_170_local_presence(self):self.assertEqual('GREEN',x.LocalPresence(True,True,True,True,('e',)).status)
 def test_171_business_model(self):
  self.assertEqual(('GREEN',()),x.business_model_status((x.BusinessFact('service','mortgage',True,'e'),),('service',)))
  self.assertEqual('HUMAN_REQUIRED',x.business_model_status((),('service',))[0])
 def test_172_process_discovery(self):self.assertEqual('GREEN',x.process_map_status((x.ProcessNode('lead','sales','CRM',('case',)),)))
 def test_173_knowledge_bootstrap(self):
  self.assertTrue(x.BootstrapKnowledge('c','c:kb',('src',),1,1,'PROD','2.0.0').green);self.assertFalse(x.BootstrapKnowledge('c','c:kb',('src',),1,1,'DEV','2.0.0').green)
 def test_174_seo_bootstrap(self):self.assertTrue(x.SeoBootstrap(True,True,True,True,True,'gate').green)
 def test_175_social_bootstrap(self):self.assertEqual('PLAN_GREEN',x.SocialBootstrap(('p',),'tone','cal',('m',),False).status())
 def test_176_marketing_bootstrap(self):self.assertEqual('HUMAN_REQUIRED',x.MarketingBootstrap('f','p',True,'o',1,0).status())
 def test_177_crm_bootstrap(self):self.assertEqual('GREEN',x.CompanyScaffold('c','CRM','cfg',True,True,'PREPROD','2.0.0').status())
 def test_178_app_bootstrap(self):self.assertEqual('GREEN',x.CompanyScaffold('c','APP','cfg',True,True,'PREPROD','2.0.0').status())
 def test_179_automation_bootstrap(self):self.assertEqual('GREEN',x.CompanyScaffold('c','AUTOMATION','cfg',True,True,'PREPROD','2.0.0').status())
 def test_180_training_bootstrap(self):self.assertEqual('GREEN',x.TrainingBootstrap('c','ds','vocab','score',False,'LAB','2.0.0').status);self.assertEqual('BLOCKED',x.TrainingBootstrap('c','ds','v','s',True,'LAB','2.0.0').status)
 def test_181_engine_activation(self):
  req,opt=x.activation_matrix('finance',(x.ActivationRule('*',('CORE-001',),()),x.ActivationRule('finance',('VIA-001',),('SEO-001',))));self.assertEqual(('CORE-001','VIA-001'),req);self.assertEqual(('SEO-001',),opt)
 def test_182_company_deployment(self):
  self.assertTrue(x.CompanyDeployment(True,True,True,True,True,('preprod','tests','integrations','rollback','health'),'c','PROD','2.0.0').promotable)
  self.assertFalse(x.CompanyDeployment(True,True,True,True,True).promotable)
  self.assertFalse(x.CompanyDeployment(True,True,False,True,True,('e',),'c','PROD','2.0.0').promotable)
  self.assertFalse(x.CompanyDeployment(True,True,True,True,True,('e',),'c','PREPROD','2.0.0').promotable)
 def test_183_company_health(self):
  self.assertEqual('GREEN',x.CompanyHealth('c',True,True,True,True,('health-evidence',),'PROD','2.0.0').status)
  self.assertEqual('RED',x.CompanyHealth('c',True,True,True,True).status)
  self.assertEqual('RED',x.CompanyHealth('c',True,True,True,True,('e',),'DEV','2.0.0').status)
 def test_184_company_backup(self):
  b=x.CompanyBackupPack('c','m','cfg','schema','kb',True,'restore-evidence','PROD','2.0.0');self.assertTrue(b.green);self.assertTrue(b.digest)
  self.assertFalse(x.CompanyBackupPack('c','m','cfg','schema','kb',True).green)
  with self.assertRaises(ValueError):x.CompanyBackupPack('c','m','cfg','schema','kb',True,'e','DEV','2.0.0').digest
 def test_185_company_offboarding(self):
  p=x.OffboardingPlan('c','exp',True,True,True,'ret',False,'PROD','2.0.0');self.assertEqual('HUMAN_REQUIRED',p.status());self.assertEqual('GREEN',x.OffboardingPlan('c','exp',True,True,True,'ret',True,'PROD','2.0.0').status())
if __name__=='__main__':unittest.main()
