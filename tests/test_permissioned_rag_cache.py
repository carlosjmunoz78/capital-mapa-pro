import json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"cerebro-os"))
from jobs.permissioned_rag_cache import build_index,search,CacheKey,IntelligenceCache

class RagCacheTests(unittest.TestCase):
    def test_permissioned_text_search_is_company_scoped(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); inv=root/"inv"; led=root/"led"; idx=root/"idx"; inv.mkdir(); led.mkdir()
            (inv/"fenix.json").write_text(json.dumps([{
                "company_id":"fenix","knowledge_id":"k1","kind":"PUBLIC_SOURCE_POINTER",
                "source_type":"LIVE_SOURCE","source_uri":"https://fenixcapital.es/hipotecas",
                "state":"ACTIVE","content_hash":"abc","provenance_id":"prv-1","confidence":0.95
            }]),encoding="utf-8")
            (inv/"aion.json").write_text(json.dumps([{
                "company_id":"aion","knowledge_id":"k2","kind":"PUBLIC_SOURCE_POINTER",
                "source_type":"LIVE_SOURCE","source_uri":"https://aion.example/venture",
                "state":"ACTIVE","content_hash":"def","provenance_id":"prv-2","confidence":0.90
            }]),encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_KNOWLEDGE_INVENTORY_ROOT"]=str(inv)
            os.environ["CEREBRO_KNOWLEDGE_LAB_LEDGER_ROOT"]=str(led)
            os.environ["CEREBRO_RAG_INDEX_ROOT"]=str(idx)
            try:
                build_index()
                hits=search("hipotecas",company_id="fenix",allowed_company_ids={"fenix"})
                self.assertEqual(len(hits),1)
                self.assertEqual(hits[0]["company_id"],"fenix")
                with self.assertRaises(PermissionError):
                    search("venture",company_id="aion",allowed_company_ids={"fenix"})
            finally: os.environ.clear(); os.environ.update(old)

    def test_lab_candidates_are_searchable_but_not_misrepresented_as_canonical(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); inv=root/"inv"; led=root/"led"; idx=root/"idx"; inv.mkdir(); led.mkdir()
            (led/"fenix.jsonl").write_text(json.dumps({
                "company_id":"fenix","knowledge_id":"cand1","kind":"KNOWLEDGE","source_type":"LIVE_SOURCE",
                "source_uri":"https://example.com/new","state":"VALIDATED_CANDIDATE","content_hash":"xyz",
                "record_hash":"r1","provenance_id":"prv-x","confidence":0.92,
                "canonical":False,"production_ready":False
            })+"\n",encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_KNOWLEDGE_INVENTORY_ROOT"]=str(inv)
            os.environ["CEREBRO_KNOWLEDGE_LAB_LEDGER_ROOT"]=str(led)
            os.environ["CEREBRO_RAG_INDEX_ROOT"]=str(idx)
            try:
                build_index()
                hits=search("cand1",company_id="fenix",allowed_company_ids={"fenix"})
                self.assertEqual(len(hits),1)
                self.assertEqual(hits[0]["source_kind"],"LAB_LEDGER")
                self.assertFalse(hits[0]["canonical"])
                self.assertFalse(hits[0]["production_ready"])
            finally: os.environ.clear(); os.environ.update(old)

    def test_cache_is_keyed_by_company_payload_and_rule_version_with_ttl(self):
        with tempfile.TemporaryDirectory() as td:
            cache=IntelligenceCache(Path(td))
            key=CacheKey.from_payload("fenix","rag-query","v1",{"q":"hipotecas"})
            cache.put(key,{"answer":"x"},ttl_seconds=60,now=100)
            self.assertEqual(cache.get(key,now=120),{"answer":"x"})
            self.assertIsNone(cache.get(key,now=161))
            changed=CacheKey.from_payload("fenix","rag-query","v2",{"q":"hipotecas"})
            self.assertIsNone(cache.get(changed,now=120))
            other=CacheKey.from_payload("aion","rag-query","v1",{"q":"hipotecas"})
            self.assertIsNone(cache.get(other,now=120))

if __name__=="__main__": unittest.main()
