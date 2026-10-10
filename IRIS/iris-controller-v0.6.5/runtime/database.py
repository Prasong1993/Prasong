"""IRIS Control persistence layer.

The original seven tables are retained in place. New control-plane tables are
created additively so existing work/evidence records are not dropped. All writes
use SQLite transactions through connection context managers.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

_DEFAULT_DB_PATH = Path(__file__).parent / "data" / "iris.db"
DB_PATH = Path(os.environ.get("IRIS_DB_PATH")) if os.environ.get("IRIS_DB_PATH") else _DEFAULT_DB_PATH


def get_db_path() -> Path:
    env = os.environ.get("IRIS_DB_PATH")
    return Path(env) if env else DB_PATH


def set_db_path(path):
    global DB_PATH
    DB_PATH = Path(path)
    os.environ["IRIS_DB_PATH"] = str(DB_PATH)


def get_connection():
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


_SCHEMA = """
CREATE TABLE IF NOT EXISTS evidence(
 id TEXT PRIMARY KEY, status TEXT NOT NULL, topic TEXT NOT NULL, fact TEXT NOT NULL,
 source TEXT NOT NULL, verification_state TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS work_units(
 id TEXT PRIMARY KEY, title TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'CREATED',
 current_step INTEGER NOT NULL DEFAULT 0,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS step_runs(
 id INTEGER PRIMARY KEY AUTOINCREMENT, work_id TEXT NOT NULL, step INTEGER NOT NULL,
 attempt INTEGER NOT NULL, status TEXT NOT NULL, expected TEXT, actual TEXT, note TEXT,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS errors(
 id INTEGER PRIMARY KEY AUTOINCREMENT, work_id TEXT NOT NULL, step INTEGER,
 attempt INTEGER, error_type TEXT NOT NULL, message TEXT NOT NULL, expected TEXT,
 actual TEXT, root_cause TEXT, impact TEXT, correction TEXT, verification TEXT,
 prevention_rule TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS checkpoints(
 id INTEGER PRIMARY KEY AUTOINCREMENT, work_id TEXT NOT NULL, step INTEGER NOT NULL,
 state TEXT NOT NULL, snapshot TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS verifications(
 id INTEGER PRIMARY KEY AUTOINCREMENT, work_id TEXT NOT NULL, expected TEXT NOT NULL,
 actual TEXT NOT NULL, status TEXT NOT NULL, note TEXT,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS audit_log(
 id INTEGER PRIMARY KEY AUTOINCREMENT, work_id TEXT NOT NULL, action TEXT NOT NULL,
 details TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Additive control-plane schema. Legacy rows remain intact.
CREATE TABLE IF NOT EXISTS schema_migrations(
 version INTEGER PRIMARY KEY, name TEXT NOT NULL,
 applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS projects(
 project_id TEXT PRIMARY KEY, name TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'ACTIVE',
 config_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS tasks(
 task_id TEXT PRIMARY KEY, project_id TEXT, work_id TEXT, parent_task_id TEXT,
 title TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'PENDING', assignee TEXT,
 session_id TEXT, trace_id TEXT, started_at TEXT, finished_at TEXT,
 input_json TEXT NOT NULL DEFAULT '{}', output_json TEXT NOT NULL DEFAULT '{}',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(project_id) REFERENCES projects(project_id),
 FOREIGN KEY(parent_task_id) REFERENCES tasks(task_id),
 FOREIGN KEY(work_id) REFERENCES work_units(id)
);
CREATE TABLE IF NOT EXISTS task_dependencies(
 task_id TEXT NOT NULL, depends_on_task_id TEXT NOT NULL,
 dependency_type TEXT NOT NULL DEFAULT 'finish_to_start',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY(task_id, depends_on_task_id),
 FOREIGN KEY(task_id) REFERENCES tasks(task_id),
 FOREIGN KEY(depends_on_task_id) REFERENCES tasks(task_id),
 CHECK(task_id <> depends_on_task_id)
);
CREATE TABLE IF NOT EXISTS requirements(
 requirement_id TEXT PRIMARY KEY, project_id TEXT, statement TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'UNKNOWN', acceptance_json TEXT NOT NULL DEFAULT '{}',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(project_id) REFERENCES projects(project_id)
);
CREATE TABLE IF NOT EXISTS source_evidence(
 evidence_id TEXT PRIMARY KEY, project_id TEXT, requirement_id TEXT,
 status TEXT NOT NULL CHECK(status IN ('VERIFIED','RECOVERED','UNKNOWN','BLOCKED','NOT RUN')),
 source_url TEXT, source_type TEXT NOT NULL DEFAULT 'unknown',
 source_version TEXT, collected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 checked_at TEXT, fact TEXT NOT NULL, limitations TEXT NOT NULL DEFAULT '',
 content_hash TEXT, metadata_json TEXT NOT NULL DEFAULT '{}',
 FOREIGN KEY(project_id) REFERENCES projects(project_id),
 FOREIGN KEY(requirement_id) REFERENCES requirements(requirement_id)
);
CREATE TABLE IF NOT EXISTS decisions(
 decision_id TEXT PRIMARY KEY, project_id TEXT, work_id TEXT, decision TEXT NOT NULL,
 rationale TEXT NOT NULL, policy_result TEXT NOT NULL,
 evidence_refs_json TEXT NOT NULL DEFAULT '[]',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(project_id) REFERENCES projects(project_id),
 FOREIGN KEY(work_id) REFERENCES work_units(id)
);
CREATE TABLE IF NOT EXISTS evidence_links(
 evidence_id TEXT NOT NULL, target_type TEXT NOT NULL,
 target_id TEXT NOT NULL, relationship TEXT NOT NULL DEFAULT 'supports',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY(evidence_id,target_type,target_id,relationship)
);
CREATE TABLE IF NOT EXISTS tool_registry(
 tool_id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, input_schema_json TEXT NOT NULL,
 output_contract_json TEXT NOT NULL DEFAULT '{}', dependencies_json TEXT NOT NULL DEFAULT '[]',
 permission_json TEXT NOT NULL DEFAULT '{}', side_effects TEXT NOT NULL DEFAULT 'unknown',
 timeout_seconds INTEGER NOT NULL DEFAULT 60, retry_policy_json TEXT NOT NULL DEFAULT '{}',
 idempotent INTEGER NOT NULL DEFAULT 0, enabled INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS tool_calls(
 tool_call_id TEXT PRIMARY KEY, work_id TEXT, task_id TEXT, session_id TEXT, trace_id TEXT,
 tool_id TEXT, tool_name TEXT NOT NULL, status TEXT NOT NULL
 CHECK(status IN ('PENDING','RUNNING','SUCCEEDED','FAILED','TIMEOUT','UNKNOWN_OUTCOME','BLOCKED','CANCELLED')),
 input_json TEXT NOT NULL DEFAULT '{}', output_json TEXT, error_json TEXT,
 idempotency_key TEXT UNIQUE, side_effect_started INTEGER NOT NULL DEFAULT 0,
 started_at TEXT, finished_at TEXT, result_recorded_at TEXT,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(work_id) REFERENCES work_units(id),
 FOREIGN KEY(task_id) REFERENCES tasks(task_id),
 FOREIGN KEY(tool_id) REFERENCES tool_registry(tool_id)
);
CREATE TABLE IF NOT EXISTS policies(
 policy_id TEXT PRIMARY KEY, name TEXT NOT NULL, version TEXT NOT NULL,
 rule_json TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(name,version)
);
CREATE TABLE IF NOT EXISTS policy_decisions(
 policy_decision_id TEXT PRIMARY KEY, work_id TEXT, task_id TEXT, tool_call_id TEXT,
 policy_id TEXT, result TEXT NOT NULL CHECK(result IN ('ALLOW','DENY','REQUIRE_APPROVAL')),
 reason TEXT NOT NULL, evidence_refs_json TEXT NOT NULL DEFAULT '[]',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS work_events(
 event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, work_id TEXT, task_id TEXT,
 session_id TEXT, trace_id TEXT, tool_call_id TEXT, status TEXT,
 payload_json TEXT NOT NULL DEFAULT '{}',
 occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS recovery_points(
 recovery_id TEXT PRIMARY KEY, work_id TEXT NOT NULL, task_id TEXT,
 checkpoint_id INTEGER, status TEXT NOT NULL DEFAULT 'AVAILABLE',
 snapshot_json TEXT NOT NULL, resume_strategy TEXT NOT NULL DEFAULT 'MANUAL_REVIEW',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(work_id) REFERENCES work_units(id)
);
CREATE TABLE IF NOT EXISTS verification_results(
 verification_id TEXT PRIMARY KEY, work_id TEXT, task_id TEXT, subject_type TEXT NOT NULL,
 subject_id TEXT NOT NULL, status TEXT NOT NULL, expected_json TEXT, actual_json TEXT,
 verifier TEXT NOT NULL DEFAULT 'deterministic', evidence_refs_json TEXT NOT NULL DEFAULT '[]',
 details TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS runtime_state(
 state_key TEXT PRIMARY KEY, state_json TEXT NOT NULL,
 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS record_revisions(
 revision_id INTEGER PRIMARY KEY AUTOINCREMENT, table_name TEXT NOT NULL,
 record_id TEXT NOT NULL, operation TEXT NOT NULL, before_json TEXT, after_json TEXT,
 changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_tasks_project_status ON tasks(project_id,status);
CREATE INDEX IF NOT EXISTS idx_tasks_work ON tasks(work_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_work_status ON tool_calls(work_id,status);
CREATE INDEX IF NOT EXISTS idx_events_work_time ON work_events(work_id,occurred_at);
CREATE INDEX IF NOT EXISTS idx_evidence_project_status ON source_evidence(project_id,status);
"""


def init_db():
    """Create missing tables/indexes and record schema version; safe to repeat."""
    with get_connection() as conn:
        conn.executescript(_SCHEMA)
        conn.execute(
            "INSERT OR IGNORE INTO schema_migrations(version,name) VALUES(?,?)",
            (1, "additive_control_plane_schema"),
        )


def one(sql, args=()):
    with get_connection() as conn:
        row = conn.execute(sql, args).fetchone()
        return dict(row) if row else None


def many(sql, args=()):
    with get_connection() as conn:
        return [dict(row) for row in conn.execute(sql, args).fetchall()]


def record_event(event_type, work_id=None, task_id=None, session_id=None,
                 trace_id=None, tool_call_id=None, status=None, payload=None,
                 event_id=None):
    """Persist an event that actually occurred; callers supply the event ID."""
    import json
    import uuid
    identifier = event_id or str(uuid.uuid4())
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO work_events
               (event_id,event_type,work_id,task_id,session_id,trace_id,tool_call_id,status,payload_json)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (identifier, event_type, work_id, task_id, session_id, trace_id,
             tool_call_id, status, json.dumps(payload or {}, ensure_ascii=False, sort_keys=True)),
        )
    return identifier


def runtime_status(work_id=None):
    """Read live persisted state; empty values mean no event/record was found."""
    clauses, args = (" WHERE work_id=?", [work_id]) if work_id else ("", [])
    last_update = one("SELECT MAX(recorded_at) AS updated_at FROM work_events" + clauses, args)
    return {
        "database": "ok",
        "db_path": str(get_db_path()),
        "updated_at": (last_update or {}).get("updated_at"),
        "latest_event": one("SELECT * FROM work_events" + clauses + " ORDER BY recorded_at DESC LIMIT 1", args),
        "active_tool_calls": many(
            "SELECT * FROM tool_calls WHERE status IN ('PENDING','RUNNING','UNKNOWN_OUTCOME')" +
            (" AND work_id=?" if work_id else "") + " ORDER BY created_at", args
        ),
        "latest_checkpoint": one(
            "SELECT * FROM checkpoints WHERE work_id=? ORDER BY id DESC LIMIT 1" if work_id
            else "SELECT * FROM checkpoints ORDER BY id DESC LIMIT 1",
            [work_id] if work_id else [],
        ),
        "latest_verification": one(
            "SELECT * FROM verifications WHERE work_id=? ORDER BY id DESC LIMIT 1" if work_id
            else "SELECT * FROM verifications ORDER BY id DESC LIMIT 1",
            [work_id] if work_id else [],
        ),
        "latest_error": one(
            "SELECT * FROM errors WHERE work_id=? ORDER BY id DESC LIMIT 1" if work_id
            else "SELECT * FROM errors ORDER BY id DESC LIMIT 1",
            [work_id] if work_id else [],
        ),
    }
