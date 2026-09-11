import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, rel):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


learn = load("learning_control_51_54", "learning/control.py")


class Loops51To54Tests(unittest.TestCase):
    def test_loop51_learning_generates_candidates_but_never_autopromotes(self):
        engine = learn.LearningEngine("fenix")
        for i in range(3):
            engine.record(learn.OutcomeEvent("fenix", "mortgage", "ask_more_docs", "approved", f"e:{i}", True))
        candidates = engine.candidates(3)
        self.assertEqual(1, len(candidates))
        self.assertEqual("CANDIDATE_REVIEW", candidates[0].status)
        self.assertTrue(candidates[0].sensitive)
        with self.assertRaises(ValueError):
            engine.record(learn.OutcomeEvent("other", "mortgage", "x", "y", "e"))

    def test_loop52_training_is_reproducible_and_never_prod_direct(self):
        reg = learn.TrainingRegistry()
        run = learn.TrainingRun("r1", "fenix", "SALE-001", "ds-1", "git-1", "LAB", (("accuracy", 0.9),), "ci:1")
        reg.register(run)
        with self.assertRaises(ValueError):
            reg.promote_champion("r1", tribunal_approved=False, reproducible=True)
        reg.promote_champion("r1", tribunal_approved=True, reproducible=True)
        self.assertEqual("r1", reg.champion("fenix", "SALE-001").run_id)
        with self.assertRaises(ValueError):
            learn.TrainingRun("r2", "fenix", "SALE-001", "ds", "git", "PROD", (), "e").validate()

    def test_loop53_research_preserves_sources_and_cannot_write_current_knowledge(self):
        dossier = learn.ResearchDossier("fenix", "bank policy", (
            learn.ResearchSource("fenix", "official:1", "ref:1", 0.95, True),
            learn.ResearchSource("fenix", "source:2", "ref:2", 0.85, False),
        ))
        self.assertEqual("GREEN", dossier.status())
        self.assertFalse(dossier.knowledge_write_allowed())
        self.assertGreaterEqual(dossier.confidence(), 0.8)
        with self.assertRaises(ValueError):
            learn.ResearchDossier("fenix", "x", (learn.ResearchSource("other", "s", "c", 1.0),)).validate()

    def test_loop54_conversation_to_knowledge_escalates_sensitive_or_low_confidence(self):
        green = learn.ConversationExtraction("fenix", "call:1", facts=("fact",), confidence=0.95)
        self.assertEqual("GREEN", green.status())
        low = learn.ConversationExtraction("fenix", "call:2", tasks=("task",), confidence=0.5)
        self.assertEqual("HUMAN_REQUIRED", low.status())
        sensitive = learn.ConversationExtraction("fenix", "call:3", decisions=("decision",), sensitive=True)
        self.assertEqual("HUMAN_REQUIRED", sensitive.status())


if __name__ == "__main__":
    unittest.main()
