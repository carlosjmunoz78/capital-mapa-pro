"""No-network tests. Run: python -m unittest discover -s cerebro-os/engines/B2B-PROSPECT-001 -p 'test_*.py'"""
import unittest
from queue_planner import ROUTE, priority, prepare, preview_daily

class QueueTests(unittest.TestCase):
    def test_exact_order(self):
        self.assertEqual(len(ROUTE), 15)
        for i, (p, mode) in enumerate(ROUTE, 1):
            self.assertEqual(priority(p, is_capital=mode == "capital"), i)
        self.assertIsNone(priority("Córdoba", is_capital=True))
    def test_priority_and_no_send(self):
        rows = [
          {"company_id":"fenix","business_name":"Later","municipality":"Jaén","province":"Jaén","is_capital":True},
          {"company_id":"fenix","business_name":"First","municipality":"Baena","province":"Córdoba","is_capital":False},
          {"company_id":"fenix","business_name":"Next","municipality":"Úbeda","province":"Jaén","is_capital":False},
        ]
        result=prepare(rows)
        self.assertEqual([x["business_name"] for x in result["queue"]],["First","Next","Later"])
        self.assertEqual(result["emails_sent"],0)
        self.assertTrue(all(x["send_authorized"] is False for x in result["queue"]))
    def test_duplicate_salinas_and_suppression(self):
        rows=[
          {"company_id":"fenix","business_name":"Agencia X","municipality":"Baena","province":"Cordoba","is_capital":False},
          {"company_id":"fenix","business_name":"Agencia X","municipality":"Baena","province":"Cordoba","is_capital":False},
          {"company_id":"fenix","business_name":"Inmobiliaria Salinas","municipality":"Baena","province":"Cordoba","is_capital":False},
          {"company_id":"fenix","business_name":"No desea","municipality":"Baena","province":"Cordoba","is_capital":False,"suppressed":True},
        ]
        result=prepare(rows)
        self.assertEqual(result["queue_size"],1)
        self.assertEqual(len(result["held"]),3)
    def test_shared_cap_and_zero_mutation(self):
        rows=[{"priority":1,"send_authorized":False} for i in range(400)]
        planned=preview_daily(rows,verified_daily_limit=300,remaining_quota=150,reserved_for_existing=80)
        self.assertEqual(planned["available_email_slots"],70)
        self.assertEqual(planned["deferred_count"],330)
        self.assertEqual(planned["emails_sent"],0)
        self.assertFalse(planned["send_authorized"])
    def test_no_capacity_if_newsletter_reserves_all(self):
        x=preview_daily([{"priority":1}],verified_daily_limit=300,remaining_quota=20,reserved_for_existing=30)
        self.assertEqual(x["available_email_slots"],0)
    def test_invalid_quota_holds(self):
        self.assertEqual(preview_daily([],verified_daily_limit=300,remaining_quota=301,reserved_for_existing=0)["state"],"HOLD_INVALID_QUOTA")
if __name__=="__main__": unittest.main()
