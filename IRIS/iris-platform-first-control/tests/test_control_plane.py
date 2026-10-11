import tempfile
import unittest
from pathlib import Path
from runtime.control_plane import ControlPlaneError
from runtime.verified_control_plane import VerifiedControlPlane

class ControlPlaneTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "iris.sqlite3"
        self.cp = VerifiedControlPlane(self.db)
        self.project = self.cp.create_project("test project")
        self.task = self.cp.create_task(self.project["project_id"], "controlled work")
        self.tid = self.task["task_id"]

    def tearDown(self):
        self.tmp.cleanup()

    def evidence(self, status="VERIFIED", content="verified source text", claim="supports test requirement"):
        item = self.cp.add_evidence(self.tid, source_url="https://example.com/spec",
            retrieved_at="2026-10-11T00:00:00Z", content=content, status="UNKNOWN", claim=claim)
        if status == "VERIFIED":
            return self.cp.mark_evidence_verified(item["evidence_id"], verifier_id="test-verifier",
                verification_ref="fixture://source-checked", observed_sha256=item["content_sha256"])
        return item

    def authorize(self, key="once"):
        self.cp.set_plan(self.tid, [{"step":"safe step"}])
        self.cp.approve_task(self.tid, actor="test-approver", approved=True)
        return self.cp.authorize_execution(self.tid, adapter_name="fake-adapter",
            permission_granted=True, idempotency_key=key)

    def test_health_and_unique_ids(self):
        self.assertEqual(self.cp.health()["status"], "OK")
        second = self.cp.create_task(self.project["project_id"], "another task")
        self.assertNotEqual(self.tid, second["task_id"])

    def test_unknown_evidence_cannot_unlock_plan(self):
        self.evidence("UNKNOWN")
        with self.assertRaisesRegex(ControlPlaneError, "VERIFIED_EVIDENCE_REQUIRED"):
            self.cp.set_plan(self.tid, [{"step":"do work"}])

    def test_client_cannot_self_assert_verified(self):
        with self.assertRaisesRegex(ControlPlaneError, "VERIFIED_STATUS_REQUIRES_TRUSTED_VERIFIER"):
            self.cp.add_evidence(self.tid, source_url="https://example.com/spec",
                retrieved_at="2026-10-11T00:00:00Z", content="untrusted", status="VERIFIED", claim="fake verified")

    def test_verifier_digest_mismatch_is_audited(self):
        item = self.evidence("UNKNOWN")
        with self.assertRaisesRegex(ControlPlaneError, "EVIDENCE_DIGEST_MISMATCH"):
            self.cp.mark_evidence_verified(item["evidence_id"], verifier_id="test-verifier",
                verification_ref="fixture://mismatch", observed_sha256="0" * 64)
        events = self.cp.get_audit(self.tid)
        self.assertTrue(any(e["event_type"]=="EVIDENCE_VERIFICATION_FAILED" for e in events))
        self.assertEqual(self.cp.get_evidence(self.tid)[0]["status"], "UNKNOWN")

    def test_gate_authorizes_but_does_not_invoke(self):
        self.evidence()
        result = self.authorize()
        self.assertEqual(result["status"], "AUTHORIZED_FOR_ADAPTER")
        self.assertFalse(result["invocation_performed"])
        self.assertEqual(self.cp.get_task(self.tid)["status"], "EXECUTING")

    def test_denied_permission_is_audited_and_does_not_advance(self):
        self.evidence()
        self.cp.set_plan(self.tid, [{"step":"safe step"}])
        self.cp.approve_task(self.tid, actor="test-approver", approved=True)
        with self.assertRaisesRegex(ControlPlaneError, "ADAPTER_PERMISSION_DENIED"):
            self.cp.authorize_execution(self.tid, adapter_name="fake-adapter",
                permission_granted=False, idempotency_key="denied")
        self.assertEqual(self.cp.get_task(self.tid)["status"], "AUTHORIZED")
        self.assertTrue(any(e["event_type"]=="EXECUTION_DENIED" for e in self.cp.get_audit(self.tid)))

    def test_idempotency_replay_and_mismatch(self):
        self.evidence()
        first = self.authorize("one-key")
        self.assertEqual(first, self.cp.authorize_execution(self.tid, adapter_name="fake-adapter",
            permission_granted=True, idempotency_key="one-key"))
        with self.assertRaisesRegex(ControlPlaneError, "IDEMPOTENCY_KEY_REUSE_MISMATCH"):
            self.cp.authorize_execution(self.tid, adapter_name="other-adapter",
                permission_granted=True, idempotency_key="one-key")

    def test_restart_persists_task_evidence_checkpoint_and_audit(self):
        self.evidence()
        cp = self.cp.checkpoint(self.tid)
        self.cp = VerifiedControlPlane(self.db)
        self.assertEqual(self.cp.get_task(self.tid)["status"], "RECEIVED")
        self.assertEqual(cp["snapshot"]["task"]["task_id"], self.tid)
        self.assertEqual(len(self.cp.get_evidence(self.tid)), 1)
        self.assertGreaterEqual(len(self.cp.get_audit(self.tid)), 4)

    def test_success_requires_verification_reference(self):
        self.evidence()
        self.authorize("success")
        self.cp.record_execution_result(self.tid, adapter_name="fake-adapter",
            outcome="SUCCEEDED", evidence_ref="result-1")
        with self.assertRaisesRegex(ControlPlaneError, "VERIFICATION_REFERENCE_REQUIRED"):
            self.cp.verify_task(self.tid, passed=True, verification_ref=" ")
        self.assertEqual(self.cp.verify_task(self.tid, passed=True,
            verification_ref="verification-1")["status"], "COMPLETED")

    def test_unknown_outcome_blocks_without_blind_retry(self):
        self.evidence()
        self.authorize("unknown")
        self.assertEqual(self.cp.record_execution_result(self.tid,
            adapter_name="fake-adapter", outcome="UNKNOWN_OUTCOME")["status"], "BLOCKED")

    def test_recovery_resets_approval_and_does_not_replay(self):
        self.evidence()
        self.cp.set_plan(self.tid, [{"step":"safe step"}])
        self.cp.approve_task(self.tid, actor="test-approver", approved=True)
        cp = self.cp.checkpoint(self.tid)
        self.cp.authorize_execution(self.tid, adapter_name="fake-adapter",
            permission_granted=True, idempotency_key="recovery")
        self.cp.record_execution_result(self.tid, adapter_name="fake-adapter", outcome="UNKNOWN_OUTCOME")
        restored = self.cp.restore_checkpoint(self.tid, cp["checkpoint_id"], actor="test-recovery")
        self.assertEqual(restored["status"], "PLAN_READY")
        self.assertFalse(restored["approved"])
        self.assertTrue(any(e["event_type"]=="CHECKPOINT_RESTORED" for e in self.cp.get_audit(self.tid)))
        with self.assertRaisesRegex(ControlPlaneError, "EXECUTION_NOT_AUTHORIZED"):
            self.cp.authorize_execution(self.tid, adapter_name="fake-adapter",
                permission_granted=True, idempotency_key="after-restore")

    def test_audit_redacts_secret_shaped_values(self):
        self.evidence(content="safe", claim="api_key=sk-abcdefghijklmnopqr")
        audit = str(self.cp.get_audit(self.tid))
        self.assertNotIn("sk-abcdefghijklmnopqr", audit)
        self.assertIn("REDACTED", audit)


    def test_agent_action_journal_records_start_finish_redacts_and_rejects_rewrite(self):
        started = self.cp.start_agent_action(session_id="session-test", trace_id="trace-test",
            actor_id="mcp-caller-unverified", action_name="create_task", task_id=self.tid,
            inputs={"api_key":"sk-abcdefghijklmnopqr", "title":"safe task"})
        self.cp.finish_agent_action(started["action_id"], status="SUCCEEDED",
            outputs={"result":"created", "access_token":"top-secret"})
        events = self.cp.get_agent_actions(task_id=self.tid)
        matching = [event for event in events if event["action_id"] == started["action_id"]]
        self.assertEqual([event["phase"] for event in matching], ["STARTED", "FINISHED"])
        self.assertIn("REDACTED", str(matching))
        self.assertNotIn("sk-abcdefghijklmnopqr", str(matching))
        self.assertNotIn("top-secret", str(matching))
        with self.assertRaisesRegex(ControlPlaneError, "AGENT_ACTION_ALREADY_FINISHED"):
            self.cp.finish_agent_action(started["action_id"], status="FAILED")

    def test_incomplete_action_survives_restart_and_resume_context_exposes_it(self):
        started = self.cp.start_agent_action(session_id="session-crash", trace_id="trace-crash",
            actor_id="mcp-caller-unverified", action_name="external_action", task_id=self.tid,
            inputs={"target":"authorized-test-fixture"})
        self.cp = VerifiedControlPlane(self.db)
        actions = self.cp.get_agent_actions(task_id=self.tid)
        event = next(event for event in actions if event["action_id"] == started["action_id"])
        self.assertEqual(event["phase"], "STARTED")
        self.assertEqual(event["status"], "IN_PROGRESS")
        context = self.cp.get_resume_context(self.tid)
        self.assertEqual(context["task"]["task_id"], self.tid)
        self.assertTrue(any(a["action_id"] == started["action_id"] for a in context["recent_agent_actions"]))
        self.assertIn("does not capture hidden model reasoning", " ".join(context["limitations"]))

if __name__ == "__main__":
    unittest.main()
