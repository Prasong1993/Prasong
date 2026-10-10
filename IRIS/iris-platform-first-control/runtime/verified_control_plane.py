"""Trusted verification boundary for evidence state transitions.

Only trusted server-side ingestion code may call mark_evidence_verified. The
MCP-facing adapter must never expose that method directly to the model/client.
"""
from __future__ import annotations
from typing import Any
from runtime.control_plane import ControlPlane, ControlPlaneError, now

class VerifiedControlPlane(ControlPlane):
    def add_evidence(self, task_id: str, *, source_url: str, retrieved_at: str,
                     content: str, status: str, claim: str) -> dict[str, Any]:
        if status == "VERIFIED":
            raise ControlPlaneError("VERIFIED_STATUS_REQUIRES_TRUSTED_VERIFIER")
        return super().add_evidence(task_id, source_url=source_url, retrieved_at=retrieved_at,
                                    content=content, status=status, claim=claim)

    def mark_evidence_verified(self, evidence_id: str, *, verifier_id: str,
                               verification_ref: str, observed_sha256: str) -> dict[str, Any]:
        """Mark evidence VERIFIED only from trusted server-side verification code.

        observed_sha256 must be the digest of the content actually fetched and
        checked by the trusted verifier. This method is intentionally not an MCP
        tool; a client-supplied status or digest is not accepted by the adapter.
        """
        if not all(isinstance(v, str) and v.strip()
                   for v in (evidence_id, verifier_id, verification_ref, observed_sha256)):
            raise ControlPlaneError("VERIFICATION_RECEIPT_REQUIRED")
        mismatch = False
        result = None
        with self._tx() as c:
            row = c.execute(
                "SELECT e.*,t.project_id FROM evidence e JOIN tasks t ON t.task_id=e.task_id WHERE e.evidence_id=?",
                (evidence_id,),
            ).fetchone()
            if not row:
                raise ControlPlaneError("EVIDENCE_NOT_FOUND")
            if row["content_sha256"] != observed_sha256:
                self._audit(c, row["project_id"], row["task_id"], "EVIDENCE_VERIFICATION_FAILED", "BLOCKED",
                            {"evidence_id": evidence_id, "verifier_id": verifier_id,
                             "verification_ref": verification_ref, "reason": "DIGEST_MISMATCH"})
                mismatch = True
            else:
                c.execute("UPDATE evidence SET status='VERIFIED' WHERE evidence_id=?", (evidence_id,))
                self._audit(c, row["project_id"], row["task_id"], "EVIDENCE_VERIFIED", "PASS",
                            {"evidence_id": evidence_id, "verifier_id": verifier_id,
                             "verification_ref": verification_ref, "content_sha256": observed_sha256})
                result = dict(c.execute("SELECT * FROM evidence WHERE evidence_id=?", (evidence_id,)).fetchone())
        if mismatch:
            raise ControlPlaneError("EVIDENCE_DIGEST_MISMATCH")
        return result
