import sqlite3
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from console.persistent_store import ConsoleStore
from core.minimum.catalog_receipt import canonical_receipt
from core.minimum.execute_catalog import AuthorizedContext, CatalogExecution
from core.minimum.verify_execution import verify_execution
from gateway import catalog_read as catalog
from gateway.service import GatewayRequest
from governance.policy import PolicyRequest
from identity.contracts import Identity


class CatalogReceiptAcceptance(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.store = ConsoleStore(Path(directory.name) / "audit.sqlite")
        self.now = 100
        self.issuer = "fixture:tribunal"
        self.key = Ed25519PrivateKey.generate()
        self.request = GatewayRequest(catalog.COMPANY, catalog.ENGINE, catalog.CAPABILITY,
                                      catalog.ENV, catalog.VERSION)
        self.context = AuthorizedContext(
            Identity("fixture:actor", "MACHINE", "fixture:owner", catalog.COMPANY, "fixture"),
            "fixture:readback", catalog.ENGINE, catalog.ENV, catalog.VERSION, catalog.CAPABILITY,
            "fixture:grant", 90, 110,
            PolicyRequest(catalog.COMPANY, catalog.COMPANY, catalog.ENV, catalog.CAPABILITY),
        )
        self.runtime = CatalogExecution(store=self.store, resolve_context=lambda _: self.context,
                                        execution_enabled=lambda: True, clock=lambda: self.now)

    def sign_after_readback(self, expected, result):
        evidence = verify_execution(store_path=self.store.path, request_id=expected["request_id"],
                                    actor_id=expected["actor_id"], grant_ref=expected["grant_ref"],
                                    result=result, now_epoch=self.now)
        if evidence.get("status") != expected["status"] or evidence.get("result_sha256") != expected["result_sha256"]:
            return None
        body = {**expected, "observed_at": self.now, "expires_at": self.now + 1}
        return {"body": body, "signature": self.key.sign(canonical_receipt(body)).hex()}

    def execute(self, readback=None, key=None):
        return self.runtime.execute_verified(
            self.request, request_id="fixture:readback",
            read_signed_receipt=readback if readback is not None else self.sign_after_readback,
            tribunal_issuer=self.issuer,
            tribunal_public_key=(key or self.key.public_key()).public_bytes_raw(),
        )

    def assert_blocked(self, result):
        self.assertEqual(result["status"], "BLOCKED")
        self.assertNotIn("engine_ids", result)
        self.assertNotIn("receipt_ref", result)
        self.assertFalse(result["deployment_authorized"])

    def test_signed_readback_and_idempotent_replay(self):
        first = self.execute()
        second = self.execute()
        self.assertEqual(first["count"], 177)
        self.assertEqual(second["engine_ids"], first["engine_ids"])
        self.assertRegex(first["receipt_ref"], r"^sha256:[a-f0-9]{64}$")
        self.assertFalse(first["deployment_authorized"])
        self.assertEqual(self.store.counts(), {"audit": 1, "history": 1})

    def test_revocation_before_start(self):
        self.context = replace(self.context, identity=replace(self.context.identity, status="REVOKED"))
        readback = Mock()
        self.assert_blocked(self.execute(readback))
        readback.assert_not_called()
        self.assertEqual(self.store.counts(), {"audit": 0, "history": 0})

    def test_revocation_during_readback_blocks_delivery(self):
        def readback(expected, result):
            receipt = self.sign_after_readback(expected, result)
            self.assertIsNotNone(receipt)
            self.context = None
            return receipt

        self.assert_blocked(self.execute(readback))
        self.assertIsNone(self.context)
        self.assertEqual(self.store.counts(), {"audit": 1, "history": 1})

    def test_audit_write_failure_stops_before_readback(self):
        readback = Mock()
        with patch.object(ConsoleStore, "record", side_effect=sqlite3.OperationalError("offline")):
            self.assert_blocked(self.execute(readback))
        readback.assert_not_called()
        self.assertEqual(self.store.counts(), {"audit": 0, "history": 0})

    def test_readback_failure_preserves_committed_evidence(self):
        self.assert_blocked(self.execute(Mock(side_effect=OSError("offline"))))
        self.assertEqual(self.store.counts(), {"audit": 1, "history": 1})
        self.assertEqual(self.execute()["count"], 177)
        self.assertEqual(self.store.counts(), {"audit": 1, "history": 1})

    def test_changed_grant_cannot_reuse_receipt_rows(self):
        self.assertEqual(self.execute()["count"], 177)
        self.context = replace(self.context, grant_ref="fixture:other-grant")
        self.assert_blocked(self.execute())
        self.assertEqual(self.store.counts(), {"audit": 1, "history": 1})

    def test_wrong_tribunal_key_cannot_authorize_delivery(self):
        self.assert_blocked(self.execute(key=Ed25519PrivateKey.generate().public_key()))

    def test_previous_signed_receipt_cannot_satisfy_new_nonce(self):
        receipts = []

        def readback(expected, result):
            if not receipts:
                receipts.append(self.sign_after_readback(expected, result))
            return receipts[0]

        self.assertEqual(self.execute(readback)["count"], 177)
        self.assert_blocked(self.execute(readback))

    def test_expired_receipt_cannot_authorize_delivery(self):
        def readback(expected, result):
            receipt = self.sign_after_readback(expected, result)
            self.now += 1
            return receipt

        self.assert_blocked(self.execute(readback))
