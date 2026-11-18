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
    def test_brand_palette_matches_manual_2025(self):
        import re
        official={'#222222','#870064','#FFB71B','#FF5F00','#FFFFFF'}
        for kind in ('b2b','b2c'):
            s=(ENGINE/f'templates/news001_{kind}_original_lab.html').read_text(encoding='utf-8')
            colors={x.upper() for x in re.findall(r'#[0-9a-fA-F]{6}',s)}
            self.assertTrue(colors.issubset({x.upper() for x in official}))
            self.assertIn('#870064',s)
            self.assertIn('#FFB71B',s)
            self.assertIn('#FF5F00',s)
            self.assertNotIn('#142d38',s)
    def test_visual_acceptance_fail_closed_and_no_false_positive(self):
        """Color-only CI cannot approve a design that loses blocks/logo/images."""
        p=ROOT/"registry/news001_directiva_propietario_v2_20261118.json"
        r=json.loads(p.read_text(encoding="utf-8"))
        assert r["news_content"]["templates"]=="SIMPLIFIED_CANDIDATES_REJECTED"
        assert r["news_content"]["visual_qa_status"].startswith("FAILED_")
        reference=r["news_content"]["visual_reference"]
        assert reference["require_images_at_least"] >= 2
        assert reference["require_h2_at_least"] >= 8
        assert reference["require_true_logo"] is True
        assert reference["require_clickable_links_at_least"] >= 13
        for kind in ("b2b","b2c"):
            s=(ENGINE/f"templates/news001_{kind}_original_lab.html").read_text(encoding="utf-8")
            import re
            broken=(len(re.findall(r'<img\\b',s,re.I))<reference["require_images_at_least"]
                    or len(re.findall(r'<h2\\b',s,re.I))<reference["require_h2_at_least"]
                    or len(re.findall(r'<a\\b',s,re.I))<reference["require_clickable_links_at_least"])
            self.assertTrue(broken, "Rejected-simplified marker must be removed when all design gates are genuinely restored")
        self.assertFalse(r["news_content"]["brevo_send_enabled"])
    def test_no_brevo_send_ever(self):
        p=ROOT/"registry/news001_directiva_propietario_v2_20261118.json"
        r=json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(r["current_protection"]["brevo_list_mutations"],"OFF")
        self.assertIs(r["news_content"]["brevo_send_enabled"],False)

if __name__=="__main__":
    unittest.main()
