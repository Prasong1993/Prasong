"""Database-first control-plane migration and persistence checks."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runtime"))

import database


def test_additive_schema_and_event_round_trip(tmp_path, monkeypatch):
    db_file = tmp_path / "iris_migration_test.db"
    original_db_path = database.DB_PATH
    monkeypatch.setenv("IRIS_DB_PATH", str(db_file))
    try:
        database.set_db_path(db_file)
        database.init_db()
        database.init_db()
        names = {row["name"] for row in database.many("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"work_units", "evidence", "audit_log", "schema_migrations", "projects", "tasks",
                "task_dependencies", "source_evidence", "tool_registry", "tool_calls", "policies",
                "policy_decisions", "work_events", "recovery_points", "verification_results",
                "runtime_state", "record_revisions"} <= names
        database.record_event("EVIDENCE_COLLECTED", status="VERIFIED",
                              payload={"source_url": "https://example.invalid/spec", "fact": "test fixture"})
        state = database.runtime_status()
        assert state["database"] == "ok"
        assert state["latest_event"]["event_type"] == "EVIDENCE_COLLECTED"
        assert state["latest_event"]["status"] == "VERIFIED"
        database.record_event("SECOND_EVENT", status="VERIFIED", payload={"sequence": 2})
        assert database.runtime_status()["latest_event"]["event_type"] == "SECOND_EVENT"
        assert database.one("SELECT version FROM schema_migrations WHERE version=1") is not None
    finally:
        database.DB_PATH = original_db_path
