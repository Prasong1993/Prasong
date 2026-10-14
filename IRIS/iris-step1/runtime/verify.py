"""Result verification checks required evidence and a successful adapter result."""
from __future__ import annotations
from .database import connection

class VerificationError(ValueError):
    pass

def verify_task(task_id: str) -> dict:
    with connection() as c:
        task = c.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if task is None:
            raise VerificationError("TASK_NOT_FOUND")
        if task["status"] != "COMPLETED":
            raise VerificationError("TASK_NOT_COMPLETED")
        evidence = c.execute(
            "SELECT COUNT(*) AS n FROM evidence WHERE task_id=? AND kind='ADAPTER_RESULT'", (task_id,)
        ).fetchone()["n"]
        if not evidence or not task["result_json"]:
            raise VerificationError("RESULT_EVIDENCE_MISSING")
        return {"task_id": task_id, "status": "VERIFIED", "checks": ["COMPLETED", "RESULT_PERSISTED", "ADAPTER_EVIDENCE_PRESENT"]}
