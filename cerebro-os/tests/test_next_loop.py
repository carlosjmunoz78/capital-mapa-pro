import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

def load(name, rel):
    spec=importlib.util.spec_from_file_location(name, ROOT/rel)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

deps=load('deps','governance/dependency_graph.py')
prom=load('prom','governance/promotion.py')
outbox=load('outbox','runtime/outbox.py')
jobs=load('persistence_jobs','runtime/persistent_jobs.py')
vault=load('vault','identity/credential_broker.py')
connectors=load('connectors','identity/connector_registry.py')
gateway=load('gateway','console/gateway.py')
history=load('history','console/history.py')
mass=load('mass','factory/mass_scaffold.py')

class NextLoopTests(unittest.TestCase):
    def test_dependency_graph_orders_and_rejects_cycles(self):
        g=deps.DependencyGraph(); g.add('GOV-001',[]); g.add('FACT-001',['GOV-001'])
        self.assertLess(g.order().index('GOV-001'), g.order().index('FACT-001'))
        with self.assertRaises(ValueError):
            g.add('GOV-001',['FACT-001'])

    def test_promotion_requires_gates_and_scoped_evidence(self):
        s=prom.PromotionState()
        with self.assertRaises(ValueError):
            s.transition('LAB_GREEN',gates_green=True,rollback_verified=True,backup_verified=True)
        lab_refs={'tests':'ci:lab','evaluation':'eval:lab'}
        s.transition('LAB_GREEN',gates_green=True,rollback_verified=True,backup_verified=True,evidence_refs=lab_refs)
        with self.assertRaises(ValueError):
            s.transition('PREPROD_GREEN',gates_green=False,rollback_verified=True,backup_verified=True,evidence_refs={'tests':'ci:pre','evaluation':'eval:pre','rollback':'rb:pre','backup':'bk:pre'})
        with self.assertRaises(ValueError):
            s.transition('PREPROD_GREEN',gates_green=True,rollback_verified=True,backup_verified=True,evidence_refs={'tests':'ci:pre','evaluation':'eval:pre'})
        pre_refs={'tests':'ci:pre','evaluation':'eval:pre','rollback':'rb:pre','backup':'bk:pre'}
        self.assertEqual(s.transition('PREPROD_GREEN',gates_green=True,rollback_verified=True,backup_verified=True,evidence_refs=pre_refs),'PREPROD_GREEN')

    def test_outbox_idempotency_and_delivery_evidence(self):
        o=outbox.Outbox(); e=outbox.OutboxEvent('e1','c1','x','done','1.0','ref','k1')
        self.assertTrue(o.enqueue(e)); self.assertFalse(o.enqueue(e))
        with self.assertRaises(ValueError): o.mark_delivered('k1','')
        o.mark_delivered('k1','evidence:delivery:k1')
        self.assertEqual(o.delivery_evidence['k1'],'evidence:delivery:k1')
        self.assertFalse(o.enqueue(e))
        with self.assertRaises(ValueError): o.mark_delivered('missing','evidence:x')

    def test_job_store_idempotency_and_success_evidence(self):
        s=jobs.JobStore(); j=jobs.JobSpec('j1','c1','e1','ik')
        self.assertTrue(s.reserve(j)); self.assertFalse(s.reserve(j))
        with self.assertRaises(ValueError): s.complete('ik','')
        s.complete('ik','evidence:job:ik')
        self.assertEqual(s.states['ik'],'SUCCESS')
        self.assertEqual(s.evidence_refs['ik'],'evidence:job:ik')
        with self.assertRaises(ValueError): s.complete('ik','evidence:second')
        with self.assertRaises(ValueError): jobs.JobStore().complete('missing','evidence:x')

    def test_broker_never_resolves_secret(self):
        h=vault.CredentialHandle('c1','a1','github','CEREBRO/FENIX/API_TOKEN','LAB')
        result=vault.CredentialBroker().resolve(h); self.assertFalse(result['resolved'])
        with self.assertRaises(ValueError): vault.CredentialHandle('c1','a1','x','token=abc','LAB').validate()

    def test_connector_priority(self):
        r=connectors.ConnectorRegistry(); r.register(connectors.ConnectorCapability('b','c','post','BROWSER','LAB')); r.register(connectors.ConnectorCapability('a','c','post','OFFICIAL_API','LAB'))
        self.assertEqual(r.route('c','post','LAB').connector_id,'a')

    def test_gateway_human_fallback_and_scope(self):
        r=gateway.GatewayRouter({'status':'SUP-001'}); q=gateway.GatewayRequest('u','c','global','status','r1',environment='PROD',version='2.1.0')
        routed=r.route(q)
        self.assertEqual(routed['engine_id'],'SUP-001')
        self.assertEqual(routed['environment'],'PROD')
        self.assertEqual(routed['version'],'2.1.0')
        q2=gateway.GatewayRequest('u','c','global','unknown','r2'); self.assertEqual(r.route(q2)['status'],'HUMAN_REQUIRED')
        with self.assertRaises(ValueError): gateway.GatewayRequest('u','c','global','status','r3',environment='INVALID').validate()

    def test_console_history_is_company_scoped_and_green_is_evidenced(self):
        h=history.ConsoleHistory()
        with self.assertRaises(ValueError): h.append(history.HistoryEntry('r0','c1','e1','GREEN'))
        h.append(history.HistoryEntry('r1','c1','e1','GREEN','ref:1')); h.append(history.HistoryEntry('r2','c2','e1','GREEN','ref:2'))
        self.assertEqual(len(h.by_company('c1')),1)
        self.assertEqual(h.by_company('c1')[0].evidence_ref,'ref:1')

    def test_mass_scaffold_plan_rejects_duplicates(self):
        p=mass.MassScaffoldPlan([mass.EngineSpec('A','a'),mass.EngineSpec('B','b')]); self.assertEqual(len(p.output_paths()),2)
        with self.assertRaises(ValueError): mass.MassScaffoldPlan([mass.EngineSpec('A','a'),mass.EngineSpec('A','b')]).validate()

if __name__=='__main__': unittest.main()
