import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runtime"))

from facebook_prod_mutator_guard import (
    FACEBOOK_PROD_MUTATORS,
    FacebookProdExecutionEvidence,
    MutatorDecision,
    assess_facebook_prod_execution,
    mutator_ids,
)


class FacebookProdMutatorGuardTests(unittest.TestCase):
    def base(self, scenario_id=9533724, **overrides):
        data = dict(
            scenario_id=scenario_id,
            company_id="fenix-capital",
            engine_id="SOCIALP-001",
            environment="PROD",
            version="1.0.0",
            publication_id="pub-1",
            run_id="run-1",
            engine_enabled=True,
            override_authorized_once=True,
            override_record_matches=True,
            override_not_expired=True,
            idempotency_clear=True,
            explicit_publish_authorized=True,
            policy_green=True,
            target_runtime_live=True,
            rollback_proven=True,
            t48_approved=True,
            t48_version_locked=True,
            t48_hash_present=True,
        )
        data.update(overrides)
        return FacebookProdExecutionEvidence(**data)

    def test_inventory_contains_all_known_v4_mutating_targets(self):
        self.assertEqual(
            mutator_ids(),
            frozenset({9533715, 9533724, 9533532, 9533564, 9533967, 9533972}),
        )

    def test_each_mutator_is_identified_with_real_external_module(self):
        expected = {
            9533715: "facebook-pages:CreatePost",
            9533724: "facebook-pages:CreatePost",
            9533532: "facebook-pages:UploadPhoto",
            9533564: "facebook-pages:uploadAReel",
            9533967: "facebook-pages:CreatePostWithPhotos",
            9533972: "facebook-pages:UploadVideo",
        }
        self.assertEqual({k: v.make_module for k, v in FACEBOOK_PROD_MUTATORS.items()}, expected)

    def test_missing_any_core_gate_fails_closed(self):
        fields = (
            "engine_enabled",
            "override_authorized_once",
            "override_record_matches",
            "override_not_expired",
            "idempotency_clear",
            "explicit_publish_authorized",
            "policy_green",
            "target_runtime_live",
            "rollback_proven",
        )
        for field in fields:
            with self.subTest(field=field):
                result = assess_facebook_prod_execution(self.base(**{field: False}))
                self.assertEqual(result.decision, MutatorDecision.BLOCKED)
                self.assertFalse(result.external_action_allowed)

    def test_t48_mutators_require_all_t48_evidence(self):
        for scenario_id in (9533715, 9533724, 9533532):
            for field in ("t48_approved", "t48_version_locked", "t48_hash_present"):
                with self.subTest(scenario_id=scenario_id, field=field):
                    result = assess_facebook_prod_execution(self.base(scenario_id, **{field: False}))
                    self.assertEqual(result.decision, MutatorDecision.BLOCKED)
                    self.assertFalse(result.external_action_allowed)

    def test_ready_never_means_auto_execute(self):
        result = assess_facebook_prod_execution(self.base())
        self.assertEqual(result.decision, MutatorDecision.READY_FOR_EXPLICIT_EXECUTION)
        self.assertFalse(result.external_action_allowed)
        self.assertEqual(result.human_reason, "SIGNATURE_REQUIRED")

    def test_wrong_environment_blocks(self):
        result = assess_facebook_prod_execution(self.base(environment="TEST"))
        self.assertEqual(result.decision, MutatorDecision.BLOCKED)
        self.assertIn("ENVIRONMENT_NOT_PROD", result.blockers)


if __name__ == "__main__":
    unittest.main()
