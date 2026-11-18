from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
ENGINE=ROOT / "engines" / "CEREBRO-NEWS-001"
class NewsletterOriginalTemplates(unittest.TestCase):
    def test_two_distinct_new_templates(self):
        a=(ENGINE/"templates/news001_b2b_original_lab.html").read_text(encoding="utf-8")
        b=(ENGINE/"templates/news001_b2c_original_lab.html").read_text(encoding="utf-8")
        self.assertNotEqual(a,b)
        self.assertIn("INTELIGENCIA INMOBILIARIA",a)
        self.assertIn("HIPOTECAS SIN VUELTAS",b)
    def test_both_include_official_brevo_unsubscribe(self):
        for kind in ("b2b","b2c"):
            s=(ENGINE/f"templates/news001_{kind}_original_lab.html").read_text(encoding="utf-8")
            self.assertIn('href="{{ unsubscribe }}"',s)
            self.assertIn('href="{{ mirror }}"',s)
    def test_new_templates_are_nonsendable_lab(self):
        for kind in ("b2b","b2c"):
            s=(ENGINE/f"templates/news001_{kind}_original_lab.html").read_text(encoding="utf-8")
            self.assertIn("REQUIERE_REVISION_EDITORIAL",s)
            self.assertIn("NO SEND",s)
            self.assertNotIn("<img ",s.lower())
    def test_mobile_and_accessibility(self):
        for kind in ("b2b","b2c"):
            s=(ENGINE/f"templates/news001_{kind}_original_lab.html").read_text(encoding="utf-8")
            self.assertIn("max-width:640px",s)
            self.assertIn('role="presentation"',s)
            self.assertIn('lang="es"',s)
    def test_owner_decision_excludes_old_b2c(self):
        p=ROOT/"registry/news001_directiva_propietario_v2_20261118.json"
        r=json.loads(p.read_text(encoding="utf-8"))
        self.assertIs(r["b2c"]["historical_particulares_excluded_all"],True)
        self.assertIsNone(r["b2c"]["activation_at"])
        self.assertIn("any_social_network_lead_form",r["b2c"]["valid_sources"])
    def test_salinas_always_excluded(self):
        p=ROOT/"registry/news001_directiva_propietario_v2_20261118.json"
        r=json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(r["b2b"]["excluded_business"],"Salinas")
        self.assertIs(r["b2b"]["exclude_named_business_even_if_otherwise_eligible"],True)
    def test_no_brevo_send_ever(self):
        p=ROOT/"registry/news001_directiva_propietario_v2_20261118.json"
        r=json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(r["current_protection"]["brevo_list_mutations"],"OFF")
        self.assertIs(r["news_content"]["brevo_send_enabled"],False)

if __name__=="__main__":
    unittest.main()
