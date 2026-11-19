"""2026 territory, provenance, suppression and persistent no-send regression tests."""
import tempfile
import unittest
from pathlib import Path
from queue_planner import municipality_catalog, municipality_route, priority, prepare, queue_key
from persistent_queue import DiscoveryQueue

def row(name="Test Agency", city="Baena", province="Córdoba", **kw):
    return dict(company_id="fenix", business_name=name, municipality=city, province=province, **kw)

class CatalogTests(unittest.TestCase):
    def test_official_derived_catalog_all_regions(self):
        catalog=municipality_catalog()
        self.assertEqual(len(catalog),785)
        route=municipality_route()
        self.assertEqual(len(route),784)
        self.assertEqual(len({x["ine_code"] for x in route}),784)
        self.assertEqual(len([x for x in route if x["queue_priority"]=="1"]),76)
        self.assertEqual(len([x for x in route if x["queue_priority"]=="2"]),96)
        self.assertEqual(len([x for x in route if x["queue_priority"]=="15"]),1)
        self.assertEqual({int(x["queue_priority"]) for x in route},set(range(1,16)))
        self.assertEqual(catalog[("cordoba","cordoba")]["queue_priority"],"")
    def test_cordoba_capital_cannot_be_disguised_as_town(self):
        z=prepare([row(city="Córdoba",is_capital=False)])
        self.assertEqual(z["queue_size"],0)
        self.assertEqual(z["held"][0]["reason"],"CAPITAL_FLAG_CONFLICT")
        self.assertEqual(prepare([row(city="Córdoba")])["held"][0]["reason"],"OUT_OF_OWNER_ROUTE")
    def test_fabricated_city_rejected(self):
        z=prepare([row(city="Pueblo Inexistente")])
        self.assertEqual(z["held"][0]["reason"],"UNVERIFIED_MUNICIPALITY_OR_IDENTITY")
    def test_stable_key_when_email_changes(self):
        a=row(email="team@example.org"); b=row(email="new@example.org")
        self.assertEqual(queue_key(a),queue_key(b))
    def test_existing_crm_and_brevo_exclusion(self):
        z=prepare([
            row("Inmobiliaria Campillos"),
            row("Inmobiliaria Rosales"),
            row("New Shop"),
        ],existing_agencies=[{"business_name":"Inmobiliaria Campillos","municipality":"Baena"}],
          brevo_contacts=[{"business_name":"Inmobiliaria Rosales","municipality":"Baena"}])
        self.assertEqual(z["queue_size"],1)
        self.assertEqual({x["reason"] for x in z["held"]},
                         {"PROTECTED_EXISTING_COLLABORATOR","ALREADY_IN_BREVO"})
    def test_alias_salinas_unsubscribed_and_domain_dedupe(self):
        z=prepare([
            row("INMO HOGAR LUCENA",city="Lucena"),
            row("Inmobiliaria Salinas"),
            row("Baja",unsubscribed=True),
            row("Agency One",website="https://www.agency-one.es"),
            row("Agency Two",website="https://agency-one.es"),
        ],existing_agencies=[{"business_name":"Lucena Hogar Inmobiliaria","municipality":"Lucena"}])
        self.assertEqual(z["queue_size"],1)
        self.assertEqual(len(z["held"]),4)
        self.assertEqual(z["emails_sent"],0)
        self.assertTrue(all(x["send_authorized"] is False for x in z["queue"]))
    def test_unverified_legal_status_even_with_public_email(self):
        z=prepare([row(email="info@realty.example",source_url="https://example.org",
                       source_verified_at="2026-11-19")])
        self.assertEqual(z["queue"][0]["legal_contact_basis"],"UNVERIFIED")
        self.assertEqual(z["queue"][0]["contact_status"],"DISCOVERED_ONLY")
        self.assertFalse(z["queue"][0]["send_authorized"])

class PersistenceTests(unittest.TestCase):
    def test_single_784_territory_queue_survives_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/"territory.sqlite"
            s=DiscoveryQueue(db)
            self.assertEqual(s.seed_territories()["inserted"],784)
            self.assertEqual(s.seed_territories()["already_present"],784)
            self.assertEqual(sum(s.report()["territories"].values()),784)
            first=s.next_territories(1)[0]
            self.assertEqual(first["priority"],1)
            self.assertEqual(first["province"],"Córdoba")
            self.assertEqual(s.mark_territory_researched(first["ine_code"],sources_checked=0)["status"],
                             "SOURCE_REVIEW_REQUIRED")
            s.close()
            s=DiscoveryQueue(db)
            self.assertEqual(s.next_territories(1)[0]["priority"],1)
            self.assertNotEqual(s.next_territories(1)[0]["ine_code"],first["ine_code"])
            self.assertEqual(s.report()["territories"]["SOURCE_REVIEW_REQUIRED"],1)
            self.assertEqual(s.report()["territories"]["DISCOVERY_PENDING"],783)
            s.close()

    def test_spool_reopens_no_duplicate_and_tracks_cursor(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/"lab.sqlite"
            rows=prepare([row("Second",city="Úbeda",province="Jaén"),
                          row("First",city="Baena")])
            s=DiscoveryQueue(db)
            self.assertEqual(s.ingest(rows)["inserted"],2)
            self.assertEqual(s.ingest(rows)["inserted"],0)
            self.assertEqual(s.next_review()[0]["business_name"],"First")
            self.assertTrue(s.mark_reviewed(s.next_review()[0]["idempotency_key"],decision="REVIEW_PENDING"))
            self.assertEqual(s.report()["cursor"]["reviewed_count"],1)
            s.close()
            s=DiscoveryQueue(db)
            self.assertEqual(s.next_review()[0]["business_name"],"Second")
            self.assertEqual(s.report()["cursor"]["reviewed_count"],1)
            # New earlier-priority discovery is NOT skipped by cursor.
            self.assertEqual(s.ingest(prepare([row("Fresh",city="Baena")]))["inserted"],1)
            self.assertEqual(s.next_review()[0]["business_name"],"Fresh")
            s.export_checkpoint(Path(tmp)/"evidence.json")
            self.assertNotIn("business_name",(Path(tmp)/"evidence.json").read_text())
            s.close()
    def test_send_and_cross_company_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=DiscoveryQueue(Path(tmp)/"lab.sqlite")
            with self.assertRaises(ValueError):
                s.mark_reviewed("anything",decision="SEND")
            x=prepare([row()])
            x["queue"][0]["send_authorized"]=True
            with self.assertRaises(ValueError):
                s.ingest(x)
            s.close()

if __name__=="__main__":
    unittest.main()
