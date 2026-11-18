import unittest, json
from pathlib import Path
from urllib.parse import urlparse
P=Path(__file__).resolve().parents[1]
class TestLiveLinkManifest(unittest.TestCase):
 def test_exact_eight_published_links_from_wordpress(self):
  manifest=json.loads((P/"wordpress_live_links_evidence.json").read_text(encoding="utf-8"))
  sources=json.loads((P/"motor_contenidos.json").read_text(encoding="utf-8"))["audiences"]
  self.assertEqual(set(manifest["links"]),{"b2b","b2c"})
  self.assertEqual(sum(map(len,manifest["links"].values())),8)
  for kind in ("b2b","b2c"):
   found={p[0] for p in sources[kind]["urls"].values() if p[0].startswith("/")}
   proved={x["path"] for x in manifest["links"][kind]}
   self.assertEqual(found,proved)
   for entry in manifest["links"][kind]:
    self.assertTrue(entry["published"])
    self.assertEqual(entry["slug"],entry["path"].strip("/").split("/")[-1])
    u=urlparse(entry["permalink"])
    self.assertEqual((u.scheme,u.netloc,u.path),("https","fenixcapital.es",entry["path"]))
  self.assertFalse(manifest["policy"]["send_enabled"])
 def test_mailto_not_a_webpage_link(self):
  d=json.loads((P/"motor_contenidos.json").read_text(encoding="utf-8"))["audiences"]
  for kind in ("b2b","b2c"):
   self.assertTrue(d[kind]["urls"]["question"][0].startswith("mailto:"))
if __name__=="__main__":unittest.main()
