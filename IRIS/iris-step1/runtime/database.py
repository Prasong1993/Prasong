"""SQLite persistence for iris-step1. Uses a dedicated database by default."""
from __future__ import annotations
import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "iris-step1.db"

def db_path() -> str:
    return os.environ.get("IRIS_STEP1_DB_PATH", str(DEFAULT_DB))

def connect() -> sqlite3.Connection:
    path = db_path()
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn

@contextmanager
def connection():
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db() -> None:
    with connection() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
          id TEXT PRIMARY KEY, name TEXT NOT NULL, phase INTEGER NOT NULL DEFAULT 1,
          budget INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'ACTIVE',
          created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
        CREATE TABLE IF NOT EXISTS tasks (
          id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
          title TEXT NOT NULL, kind TEXT NOT NULL, input_json TEXT NOT NULL,
          status TEXT NOT NULL, result_json TEXT, error TEXT,
          attempts INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
          updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
        CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
        CREATE TABLE IF NOT EXISTS evidence (
          id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL REFERENCES tasks(id),
          kind TEXT NOT NULL, payload_json TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
        CREATE TABLE IF NOT EXISTS audit (
          id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, action TEXT NOT NULL,
          from_status TEXT, to_status TEXT, detail TEXT NOT NULL DEFAULT '{}',
          created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
        """)
