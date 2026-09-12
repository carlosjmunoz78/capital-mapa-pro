import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from youtube_aux_prod_contract import (
    YouTubeAuxReceipt,
    YouTubeAuxRequest,
    inventory,
    normalize_youtube_aux_receipt,
    validate_youtube_aux,
)


class YouTubeAuxProdContractTests(unittest.TestCase):
    def base(self, scenario_id: int, **changes):
        data = dict(
            scenario_id=scenario_id,
            company_id="fenix-capital",
            engine_id="YOUTUBE-PROD-AUX",
            environment="PROD",
            version="1.0.0",
            publication_id="PUB1",
            run_id="RUN1",
            video_id="VID1",
            engine_enabled=True,
            override_authorized_once=True,
            override_record_matches=True,
            idempotency_clear=True,
            qa_passed=True,
            authorized=True,
            thumbnail_data_present=scenario_id == 9537710,
            playlist_id="PL1" if scenario_id == 9537718 else "",
        )
        data.update(changes)
        return YouTubeAuxRequest(**data)

    def test_inventory_has_thumbnail_and_playlist(self):
        self.assertEqual(inventory(), {9537710: "thumbnail", 9537718: "playlist"})

    def test_ready_never_autoexecutes(self):
        for scenario_id in inventory():
            out = validate_youtube_aux(self.base(scenario_id))
            self.assertEqual(out["status"], "READY_FOR_EXPLICIT_EXECUTION")
            self.assertFalse(out["external_action_allowed"])
            self.assertFalse(out["youtube_called_by_runtime"])
            self.assertEqual(out["human_reason"], "SIGNATURE_REQUIRED")

    def test_contract_specific_missing_input_blocks(self):
        thumb = validate_youtube_aux(self.base(9537710, thumbnail_data_present=False))
        playlist = validate_youtube_aux(self.base(9537718, playlist_id=""))
        self.assertIn("THUMBNAIL_DATA_REQUIRED", thumb["blockers"])
        self.assertIn("PLAYLIST_ID_REQUIRED", playlist["blockers"])

    def test_receipts_commit_only_on_platform_success(self):
        ok = normalize_youtube_aux_receipt(YouTubeAuxReceipt(9537710, "PUB1", "R1", "V1", True))
        fail = normalize_youtube_aux_receipt(YouTubeAuxReceipt(9537718, "PUB1", "R1", "V1", False))
        self.assertEqual(ok["idempotency_state"], "COMPLETED")
        self.assertEqual(fail["idempotency_state"], "OPEN")
        self.assertFalse(fail["retry_external_action_allowed"])

    def test_fixture_matches_live_contract(self):
        path = ROOT / "runtime" / "fixtures" / "youtube_aux_live_contract_2026-09-12.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(len(data["scenarios"]), 2)
        self.assertTrue(data["runtime_invariants"]["old_preserved"])
        self.assertFalse(data["runtime_invariants"]["external_action_allowed"])


if __name__ == "__main__":
    unittest.main()
