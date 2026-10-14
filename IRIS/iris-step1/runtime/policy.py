"""Deterministic admission policy."""
from __future__ import annotations
import json
from .database import connection

class PolicyError(ValueError):
    pass

def check_project(project_id: str) -> dict:
    with connection() as c:
        row = c.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    if row is None:
        raise PolicyError("PROJECT_NOT_FOUND")
    project = dict(row)
    if project["status"] != "ACTIVE":
        raise PolicyError("PROJECT_NOT_ACTIVE")
    if project["phase"] < 1:
        raise PolicyError("INVALID_PHASE")
    return project

def check_task(project_id: str, title: str, kind: str) -> None:
    check_project(project_id)
    if not title.strip():
        raise PolicyError("EMPTY_TITLE")
    if not kind.strip() or len(kind) > 80:
        raise PolicyError("INVALID_KIND")
    with connection() as c:
        duplicate = c.execute(
            "SELECT 1 FROM tasks WHERE project_id=? AND lower(title)=lower(?) AND status NOT IN ('FAILED','BLOCKED') LIMIT 1",
            (project_id, title.strip())
        ).fetchone()
    if duplicate:
        raise PolicyError("DUPLICATE_ACTIVE_TASK")
