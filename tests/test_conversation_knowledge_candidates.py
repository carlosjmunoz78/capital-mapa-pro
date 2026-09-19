import json,os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"cerebro-os"))
from jobs.prepare_conversation_knowledge_candidates import normalize_conversation,run

class ConversationKnowledgeTests(unittest.TestCase):
    def _base(self):
        return {
            "company_id":"fenix","conversation_id":"conv-1","environment":"LAB","version":"1.0.0",
            "source_type":"INTERNAL_DOCUMENT","source_uri":"conversation://conv-1","observed_at":"2026-09-19T18:00:00+00:00",
            "items":[]
        }

    def test_high_confidence_general_fact_is_candidate_only(self):
        p=self._base(); p["items"]=[{"type":"FACT","text":"Cliente solicita llamada mañana","confidence":0.94,"domain":"CUSTOMER","speaker_ref":"customer"}]
        out=normalize_conversation(p)
        c=out["candidates"][0]
        self.assertEqual(c["status"],"CANDIDATE_ONLY")
        self.assertIsNone(c["human_reason"])
        self.assertFalse(c["knowledge_write_allowed"])
        self.assertTrue(c["requires_provenance_validation"])
        self.assertIn("PRV-001",c["required_gates"])
        self.assertFalse(out["raw_text_extraction_performed"])

    def test_low_confidence_routes_to_human_exception(self):
        p=self._base(); p["items"]=[{"type":"DECISION","text":"Parece que se aceptó una condición","confidence":0.55,"domain":"GENERAL"}]
        c=normalize_conversation(p)["candidates"][0]
        self.assertEqual(c["status"],"HUMAN_REQUIRED")
        self.assertEqual(c["human_reason"],"LOW_CONFIDENCE")

    def test_legal_item_never_auto_promotes(self):
        p=self._base(); p["items"]=[{"type":"COMMITMENT","text":"Firmar documento legal","confidence":0.99,"domain":"LEGAL"}]
        c=normalize_conversation(p)["candidates"][0]
        self.assertEqual(c["status"],"HUMAN_REQUIRED")
        self.assertEqual(c["human_reason"],"LEGAL_REQUIRED")
        self.assertFalse(c["auto_promote_allowed"])
        self.assertFalse(c["external_mutation_allowed"])

    def test_file_job_keeps_company_namespace(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); src=root/"src"; out=root/"out"; src.mkdir()
            p=self._base(); p["items"]=[{"type":"TASK","text":"Enviar resumen","confidence":0.9,"domain":"GENERAL"}]
            (src/"one.json").write_text(json.dumps(p),encoding="utf-8")
            old=os.environ.copy()
            os.environ["CEREBRO_CONVERSATION_STRUCTURED_ROOT"]=str(src)
            os.environ["CEREBRO_CONVERSATION_KNOWLEDGE_ROOT"]=str(out)
            try: run()
            finally: os.environ.clear(); os.environ.update(old)
            self.assertTrue((out/"fenix"/"conv-1.json").exists())

if __name__=="__main__": unittest.main()
