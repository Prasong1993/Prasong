import hashlib
import tempfile
import unittest
from pathlib import Path
from runtime.control_plane import ControlPlaneError
from runtime.verified_control_plane import VerifiedControlPlane
from runtime.source_verifier import SourceVerifier

class SourceVerifierTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cp = VerifiedControlPlane(Path(self.tmp.name) / "iris.sqlite3")
        self.project = self.cp.create_project("evidence project")
        self.task = self.cp.create_task(self.project["project_id"], "verify source")
        self.tid = self.task["task_id"]
        self.body = b"Official documentation body for a test."
        self.verifier = SourceVerifier(self.cp, allowed_hosts={"docs.example.test"},
            fetcher=lambda url: (200, "text/html", self.body))

    def tearDown(self):
        self.tmp.cleanup()

    def test_fetches_allowlisted_https_and_marks_source_verified(self):
        result = self.verifier.ingest(self.tid, source_url="https://docs.example.test/guide", claim="source contains documentation")
        self.assertEqual(result["status"], "VERIFIED")
        self.assertEqual(result["verification_scope"], "SOURCE_RETRIEVAL_AND_CONTENT_DIGEST_ONLY")
        self.assertEqual(result["evidence"]["content_sha256"], hashlib.sha256(self.body).hexdigest())
        self.assertEqual(self.cp.get_evidence(self.tid)[0]["status"], "VERIFIED")

    def test_untrusted_host_rejected_before_fetch_and_audited(self):
        with self.assertRaisesRegex(ControlPlaneError, "SOURCE_HOST_NOT_ALLOWLISTED"):
            self.verifier.ingest(self.tid, source_url="https://untrusted.example/secret", claim="test")
        self.assertTrue(any(e["event_type"] == "SOURCE_VERIFICATION_FAILED" for e in self.cp.get_audit(self.tid)))

    def test_query_parameters_rejected_to_avoid_secret_leaks(self):
        with self.assertRaisesRegex(ControlPlaneError, "SOURCE_URL_QUERY_NOT_ALLOWED"):
            self.verifier.ingest(self.tid, source_url="https://docs.example.test/guide?token=secret", claim="test")

    def test_redirect_or_non_200_response_fails_closed(self):
        verifier = SourceVerifier(self.cp, allowed_hosts={"docs.example.test"}, fetcher=lambda url: (302, "text/html", b"redirect"))
        with self.assertRaisesRegex(ControlPlaneError, "SOURCE_HTTP_STATUS_302"):
            verifier.ingest(self.tid, source_url="https://docs.example.test/guide", claim="test")
        self.assertTrue(any(e["status"] == "BLOCKED" for e in self.cp.get_evidence(self.tid)))

    def test_oversized_body_is_rejected(self):
        verifier = SourceVerifier(self.cp, allowed_hosts={"docs.example.test"}, max_bytes=8,
            fetcher=lambda url: (200, "text/plain", b"0123456789"))
        with self.assertRaisesRegex(ControlPlaneError, "SOURCE_BODY_TOO_LARGE"):
            verifier.ingest(self.tid, source_url="https://docs.example.test/guide", claim="test")

if __name__ == "__main__":
    unittest.main()
