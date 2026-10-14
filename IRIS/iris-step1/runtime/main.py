"""iris-step1 API: approval-gated tasks with persistent evidence and audit."""
from __future__ import annotations
import json
import uuid
from typing import Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .database import connection, init_db
from .policy import PolicyError, check_project, check_task
from .task_queue import get_adapter
from .verify import VerificationError, verify_task

app = FastAPI(title="iris-step1", version="0.1.0")

@app.on_event("startup")
def startup() -> None:
    init_db()

class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    phase: int = Field(default=1, ge=1)
    budget: int = Field(default=0, ge=0)

class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    kind: str = Field(min_length=1, max_length=80)
    input: dict[str, Any] = Field(default_factory=dict)

def audit(task_id: str | None, action: str, old: str | None, new: str | None, detail: dict | None = None) -> None:
    with connection() as c:
        c.execute("INSERT INTO audit(task_id,action,from_status,to_status,detail) VALUES(?,?,?,?,?)",
                  (task_id, action, old, new, json.dumps(detail or {}, sort_keys=True)))

def get_task(task_id: str) -> dict:
    with connection() as c:
        row = c.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "TASK_NOT_FOUND")
    item = dict(row)
    item["input"] = json.loads(item.pop("input_json"))
    item["result"] = json.loads(item.pop("result_json")) if item.get("result_json") else None
    return item

def transition(task_id: str, expected: str, target: str, action: str, detail: dict | None = None) -> None:
    with connection() as c:
        row = c.execute("SELECT status FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "TASK_NOT_FOUND")
        if row["status"] != expected:
            raise HTTPException(409, f"INVALID_STATE:{row['status']} expected {expected}")
        c.execute("UPDATE tasks SET status=?, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?",
                  (target, task_id))
        c.execute("INSERT INTO audit(task_id,action,from_status,to_status,detail) VALUES(?,?,?,?,?)",
                  (task_id, action, expected, target, json.dumps(detail or {}, sort_keys=True)))

@app.get("/")
def root():
    return {"service": "iris-step1", "version": "0.1.0", "status": "source-in-progress"}

@app.get("/health")
def health():
    init_db()
    return {"status": "ok", "database": "initialized"}

@app.post("/projects", status_code=201)
def create_project(body: ProjectIn):
    project_id = str(uuid.uuid4())
    with connection() as c:
        c.execute("INSERT INTO projects(id,name,phase,budget) VALUES(?,?,?,?)",
                  (project_id, body.name.strip(), body.phase, body.budget))
    audit(None, "PROJECT_CREATED", None, "ACTIVE", {"project_id": project_id})
    return {"id": project_id, "name": body.name.strip(), "phase": body.phase, "budget": body.budget, "status": "ACTIVE"}

@app.get("/projects/{project_id}")
def read_project(project_id: str):
    try:
        with connection() as c:
            row = c.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        if row is None: raise HTTPException(404, "PROJECT_NOT_FOUND")
        project = dict(row)
        with connection() as c:
            project["tasks_count"] = c.execute("SELECT COUNT(*) FROM tasks WHERE project_id=?", (project_id,)).fetchone()[0]
        return project
    except sqlite3.Error as exc:
        raise HTTPException(500, str(exc))

@app.post("/projects/{project_id}/tasks", status_code=201)
def create_task(project_id: str, body: TaskIn):
    try:
        check_task(project_id, body.title, body.kind)
    except PolicyError as exc:
        code = str(exc)
        raise HTTPException(404 if code == "PROJECT_NOT_FOUND" else 409, code)
    task_id = str(uuid.uuid4())
    with connection() as c:
        c.execute("INSERT INTO tasks(id,project_id,title,kind,input_json,status) VALUES(?,?,?,?,?,'QUEUED')",
                  (task_id, project_id, body.title.strip(), body.kind, json.dumps(body.input, sort_keys=True)))
        c.execute("INSERT INTO audit(task_id,action,from_status,to_status,detail) VALUES(?,?,?,?,?)",
                  (task_id, "TASK_CREATED", None, "QUEUED", "{}"))
    return get_task(task_id)

@app.get("/tasks/{task_id}")
def read_task(task_id: str):
    return get_task(task_id)

@app.post("/tasks/{task_id}/approve")
def approve(task_id: str):
    task = get_task(task_id)
    try: check_project(task["project_id"])
    except PolicyError as exc: raise HTTPException(409, str(exc))
    transition(task_id, "QUEUED", "APPROVED", "TASK_APPROVED", {"approval": "explicit-api-call"})
    return get_task(task_id)

@app.post("/tasks/{task_id}/execute")
def execute(task_id: str):
    task = get_task(task_id)
    if task["status"] != "APPROVED":
        raise HTTPException(409, f"INVALID_STATE:{task['status']} expected APPROVED")
    adapter = get_adapter(task["kind"])
    if adapter is None:
        transition(task_id, "APPROVED", "BLOCKED", "EXECUTION_BLOCKED", {"reason": "NO_REGISTERED_ADAPTER", "executed": False})
        raise HTTPException(409, "NO_REGISTERED_ADAPTER; execution was not performed")
    transition(task_id, "APPROVED", "RUNNING", "EXECUTION_STARTED")
    try:
        result = adapter(task["input"])
        if not isinstance(result, dict):
            raise TypeError("Adapter must return a dict")
        with connection() as c:
            c.execute("UPDATE tasks SET result_json=?, attempts=attempts+1, status='COMPLETED', updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=? AND status='RUNNING'",
                      (json.dumps(result, sort_keys=True), task_id))
            c.execute("INSERT INTO evidence(task_id,kind,payload_json) VALUES(?,?,?)",
                      (task_id, "ADAPTER_RESULT", json.dumps({"result": result}, sort_keys=True)))
            c.execute("INSERT INTO audit(task_id,action,from_status,to_status,detail) VALUES(?,?,?,?,?)",
                      (task_id, "EXECUTION_COMPLETED", "RUNNING", "COMPLETED", json.dumps({"result_persisted": True})))
    except Exception as exc:
        transition(task_id, "RUNNING", "FAILED", "EXECUTION_FAILED", {"error": type(exc).__name__})
        raise HTTPException(500, "ADAPTER_EXECUTION_FAILED")
    return get_task(task_id)

@app.post("/tasks/{task_id}/verify")
def verify(task_id: str):
    try: result = verify_task(task_id)
    except VerificationError as exc: raise HTTPException(409, str(exc))
    transition(task_id, "COMPLETED", "VERIFIED", "TASK_VERIFIED", result)
    return result

@app.post("/tasks/{task_id}/deliver")
def deliver(task_id: str):
    transition(task_id, "VERIFIED", "DELIVERED", "TASK_DELIVERED")
    return get_task(task_id)

@app.post("/tasks/{task_id}/fail")
def fail(task_id: str, reason: str = "MANUAL_FAILURE"):
    task = get_task(task_id)
    if task["status"] not in ("QUEUED", "APPROVED", "RUNNING"):
        raise HTTPException(409, f"CANNOT_FAIL_FROM:{task['status']}")
    transition(task_id, task["status"], "FAILED", "TASK_FAILED", {"reason": reason[:300]})
    return get_task(task_id)

@app.get("/tasks/{task_id}/evidence")
def task_evidence(task_id: str):
    get_task(task_id)
    with connection() as c:
        rows = c.execute("SELECT * FROM evidence WHERE task_id=? ORDER BY id", (task_id,)).fetchall()
    return [dict(r, payload=json.loads(r["payload_json"])) for r in rows]

@app.get("/audit")
def read_audit(task_id: str | None = None, limit: int = 100):
    limit = max(1, min(limit, 500))
    with connection() as c:
        if task_id:
            rows = c.execute("SELECT * FROM audit WHERE task_id=? ORDER BY id DESC LIMIT ?", (task_id, limit)).fetchall()
        else:
            rows = c.execute("SELECT * FROM audit ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r, detail_json=json.loads(r["detail"])) for r in rows]
