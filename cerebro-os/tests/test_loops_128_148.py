import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(n,r):
 p=ROOT/r;s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
p=load('platform_engines_128_148','platform/engines.py')
data=load('data_contract_128','data/contracts.py')
deps=load('dep_graph_128','governance/dependency_graph.py')
conn=load('connector_registry_128','connectors/registry.py')
gw=load('gateway_service_128','gateway/service.py')
route=load('zero_cost_128','routing/zero_cost.py')
class T(unittest.TestCase):
 def test_128_app_wrapper_preserves_snapshot_and_gates_change(self):
  c=p.LegacyContract('APP','1.0',('r',),('w',),'snap');c.validate();self.assertFalse(c.change_allowed(True,False,True));self.assertFalse(c.change_allowed(True,True,True));self.assertTrue(c.change_allowed(True,True,True,{'tests':'ci:1','rollback':'rb:1','scope':'scope:1'}))
 def test_129_crm_wrapper_preserves_snapshot_and_gates_change(self):
  c=p.LegacyContract('CRM','1.0',('r',),('w',),'snap');self.assertFalse(c.change_allowed(True,True,True));self.assertTrue(c.change_allowed(True,True,True,{'tests':'ci:1','rollback':'rb:1','scope':'scope:1'}))
 def test_130_data_contract_multicompany(self):
  c=data.DataContract('DATA-001','case','1.0',True,'schema','APP',('CRM',));self.assertTrue(c.safe_for_multicompany())
 def test_131_api_gateway_routes_known_escalates_missing_and_is_version_scoped(self):
  r=conn.ConnectorRegistry();r.register(conn.ConnectorCapability('generic','read','OFFICIAL_API'));r.register(conn.ConnectorCapability('v2','read','OFFICIAL_API','f',True,'PROD','2.0.0'));g=gw.Gateway({'API-001'},r)
  self.assertEqual('generic',g.route(gw.GatewayRequest('f','API-001','read'))['connector_id']);self.assertEqual('v2',g.route(gw.GatewayRequest('f','API-001','read','PROD','2.0.0'))['connector_id']);self.assertEqual('generic',g.route(gw.GatewayRequest('f','API-001','read','PROD','1.0.0'))['connector_id']);self.assertEqual('HUMAN_REQUIRED',g.route(gw.GatewayRequest('f','X','read'))['status'])
 def test_132_dependency_graph_orders_and_rejects_cycle(self):
  g=deps.DependencyGraph();g.add('DATA-001',[]);g.add('API-001',['DATA-001']);self.assertLess(g.order().index('DATA-001'),g.order().index('API-001'))
  with self.assertRaises(ValueError):g.add('DATA-001',['API-001'])
 def test_133_architecture_findings_score(self):
  self.assertEqual(7,p.architecture_score((p.ArchitectureFinding('DRIFT','x','e',3),p.ArchitectureFinding('COUPLING','y','e',4))))
 def test_134_debt_priority(self):
  self.assertEqual(3.0,p.DebtItem('d',4,2,2,'e').priority)
 def test_135_migration_requires_up_down_test_backup_rollback_evidence(self):
  self.assertFalse(p.MigrationPlan('m','up','down','test','bkp',True).green);self.assertTrue(p.MigrationPlan('m','up','down','test','bkp',True,'rb:test').green);self.assertFalse(p.MigrationPlan('m','up','down','test','bkp',False,'rb:test').green)
 def test_136_feature_flag_percentage_role_environment(self):
  f=p.FeatureFlag('new','LAB',10,frozenset({'admin'}));self.assertTrue(f.enabled(5,'admin'));self.assertFalse(f.enabled(15,'admin'));self.assertFalse(f.enabled(5,'user'))
 def test_137_canary_promotes_or_rolls_back_with_metric_evidence(self):
  self.assertEqual('BLOCKED',p.CanaryStage(10,.99,.95,'rb').decision());self.assertEqual('PROMOTE',p.CanaryStage(10,.99,.95,'rb','metric:e').decision());self.assertEqual('ROLLBACK',p.CanaryStage(50,.8,.95,'rb','metric:e').decision())
 def test_138_model_route_prefers_deterministic_free_first(self):
  d=route.choose_route((route.ExecutionOption('PAID',True,1),route.ExecutionOption('DETERMINISTIC',True,0)),'NORMAL',0);self.assertEqual('DETERMINISTIC',d.route_type)
 def test_139_local_first_precedes_external(self):
  d=route.choose_route((route.ExecutionOption('CHEAP_EXTERNAL',True,0),route.ExecutionOption('LOCAL',True,0)),'OCR_HEAVY',0);self.assertEqual('LOCAL',d.route_type);self.assertTrue(d.offload_from_supabase)
 def test_140_ai_budget_blocks_unapproved_cost(self):
  d=route.choose_route((route.ExecutionOption('PAID',True,.01),),'NORMAL',0);self.assertFalse(d.allowed);self.assertEqual('MONEY_LIMIT',d.reason)
 def test_141_resource_optimization_generates_safe_actions(self):
  a=p.optimization_actions((p.ResourceUsage('j',True,True,100,'e'),));self.assertEqual(('COMPACT:j:100','DEDUP:j','STOP_IDLE:j'),a)
 def test_142_automation_engine_only_plans_positive_roi_low_risk(self):
  self.assertEqual('PLAN',p.AutomationCandidate('x',20,30,2,'LOW').decision());self.assertEqual('HUMAN_REQUIRED',p.AutomationCandidate('x',20,30,2,'HIGH').decision())
 def test_143_docs_gate_requires_all_canonical_docs_and_evidence(self):
  self.assertEqual('BLOCKED',p.docs_gate({x:True for x in p.REQUIRED_DOCS}));self.assertEqual('GREEN',p.docs_gate({x:f'doc:{x}' for x in p.REQUIRED_DOCS}));self.assertEqual('BLOCKED',p.docs_gate({'engine_registry':'doc:registry'}))
 def test_144_web_change_never_direct_prod_and_requires_evidence(self):
  self.assertEqual('RED',p.WebChange('w',True,True,True,'rb','PREPROD').decision());self.assertEqual('GREEN',p.WebChange('w',True,True,True,'rb','PREPROD','bkp:e','tests:e','seo:e').decision());self.assertEqual('BLOCKED',p.WebChange('w',True,True,True,'rb','PROD','bkp:e','tests:e','seo:e').decision())
 def test_145_integration_inventory_rejects_embedded_secret(self):
  p.IntegrationRecord('x',('a',),('b',),'owner','GREEN','vault://x').validate()
  with self.assertRaises(ValueError):p.IntegrationRecord('x',(),(),'owner','GREEN','token=abc').validate()
 def test_146_database_offload_marks_heavy_workloads(self):
  d=route.choose_route((route.ExecutionOption('LOCAL',True,0),),'TRAINING',0);self.assertTrue(d.offload_from_supabase)
 def test_147_storage_offload_marks_backup_heavy(self):
  d=route.choose_route((route.ExecutionOption('LOCAL',True,0),),'BACKUP',0);self.assertTrue(d.offload_from_supabase)
 def test_148_zero_cost_broker_order(self):
  self.assertEqual(('DETERMINISTIC','LOCAL','EXISTING_TOOL','FREE_TIER','SELF_HOSTED','CHEAP_EXTERNAL','PAID'),route.ROUTE_ORDER)
if __name__=='__main__':unittest.main()
