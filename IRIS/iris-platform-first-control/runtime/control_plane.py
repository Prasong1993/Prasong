"""Deterministic, model-independent IRIS control-plane core."""
from __future__ import annotations
import hashlib, json, re, sqlite3, uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

SCHEMA_VERSION = 1
EVIDENCE_STATUSES = {"VERIFIED", "RECOVERED", "UNKNOWN", "BLOCKED", "NOT RUN"}
SECRET_KEY = re.compile(r"(?i)(secret|api[_-]?key|token|password|authorization)")
SECRET_TEXT = re.compile(r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|password|authorization)\s*[:=]\s*[^\s,;]+|\bsk-[A-Za-z0-9_-]{12,}\b")

def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def js(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): ("[REDACTED]" if SECRET_KEY.search(str(k)) else redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        return SECRET_TEXT.sub("[REDACTED]", value)
    return value

class ControlPlaneError(Exception):
    """Deterministic policy/state error safe to translate at a host boundary."""

class ControlPlane:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _conn(self):
        c = sqlite3.connect(self.db_path, timeout=10, isolation_level=None)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("PRAGMA busy_timeout=10000")
        return c

    @contextmanager
    def _tx(self) -> Iterator[sqlite3.Connection]:
        c = self._conn()
        try:
            c.execute("BEGIN IMMEDIATE")
            yield c
            c.commit()
        except Exception:
            c.rollback()
            raise
        finally:
            c.close()

    def _init(self):
        with self._tx() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS schema_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS projects(project_id TEXT PRIMARY KEY,name TEXT NOT NULL,created_at TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'ACTIVE');
            CREATE TABLE IF NOT EXISTS tasks(task_id TEXT PRIMARY KEY,project_id TEXT NOT NULL REFERENCES projects(project_id),title TEXT NOT NULL,status TEXT NOT NULL,revision INTEGER NOT NULL DEFAULT 1,approved INTEGER NOT NULL DEFAULT 0,plan_json TEXT NOT NULL DEFAULT '[]',created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS evidence(evidence_id TEXT PRIMARY KEY,task_id TEXT NOT NULL REFERENCES tasks(task_id),source_url TEXT NOT NULL,retrieved_at TEXT NOT NULL,content_sha256 TEXT NOT NULL,status TEXT NOT NULL,claim TEXT NOT NULL,created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS checkpoints(checkpoint_id TEXT PRIMARY KEY,task_id TEXT NOT NULL REFERENCES tasks(task_id),revision INTEGER NOT NULL,snapshot_json TEXT NOT NULL,created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audit_events(event_id INTEGER PRIMARY KEY AUTOINCREMENT,project_id TEXT NOT NULL,task_id TEXT,occurred_at TEXT NOT NULL,event_type TEXT NOT NULL,status TEXT NOT NULL,payload_json TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS agent_action_events(event_id INTEGER PRIMARY KEY AUTOINCREMENT,action_id TEXT NOT NULL,session_id TEXT NOT NULL,trace_id TEXT NOT NULL,project_id TEXT,task_id TEXT,actor_id TEXT NOT NULL,action_name TEXT NOT NULL,occurred_at TEXT NOT NULL,phase TEXT NOT NULL,status TEXT NOT NULL,payload_json TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS idx_agent_action_task ON agent_action_events(task_id,event_id);
            CREATE INDEX IF NOT EXISTS idx_agent_action_trace ON agent_action_events(trace_id,event_id);
            CREATE TABLE IF NOT EXISTS idempotency(idempotency_key TEXT PRIMARY KEY,operation TEXT NOT NULL,request_sha256 TEXT NOT NULL,result_json TEXT NOT NULL,created_at TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
            CREATE INDEX IF NOT EXISTS idx_evidence_task ON evidence(task_id);
            CREATE INDEX IF NOT EXISTS idx_audit_task ON audit_events(task_id,event_id);
            """)
            c.execute("INSERT OR REPLACE INTO schema_meta VALUES('schema_version',?)", (str(SCHEMA_VERSION),))

    def _audit(self,c,pid,tid,event,status,payload):
        c.execute("INSERT INTO audit_events(project_id,task_id,occurred_at,event_type,status,payload_json) VALUES(?,?,?,?,?,?)",
                  (pid,tid,now(),event,status,js(redact(payload))))

    def health(self):
        with self._conn() as c:
            r=c.execute("SELECT value FROM schema_meta WHERE key='schema_version'").fetchone()
            return {"status":"OK","schema_version":int(r["value"]) if r else None}

    def create_project(self,name):
        if not isinstance(name,str) or not name.strip(): raise ControlPlaneError("PROJECT_NAME_REQUIRED")
        pid,t=str(uuid.uuid4()),now()
        with self._tx() as c:
            c.execute("INSERT INTO projects VALUES(?,?,?,'ACTIVE')",(pid,name.strip(),t))
            self._audit(c,pid,None,"PROJECT_CREATED","PASS",{"name":name.strip()})
        return {"project_id":pid,"name":name.strip(),"status":"ACTIVE","created_at":t}

    def create_task(self,project_id,title):
        if not isinstance(title,str) or not title.strip(): raise ControlPlaneError("TASK_TITLE_REQUIRED")
        tid,t=str(uuid.uuid4()),now()
        with self._tx() as c:
            p=c.execute("SELECT status FROM projects WHERE project_id=?",(project_id,)).fetchone()
            if not p: raise ControlPlaneError("PROJECT_NOT_FOUND")
            if p["status"]!="ACTIVE": raise ControlPlaneError("PROJECT_NOT_ACTIVE")
            c.execute("INSERT INTO tasks(task_id,project_id,title,status,created_at,updated_at) VALUES(?,?,?,?,?,?)",(tid,project_id,title.strip(),"RECEIVED",t,t))
            self._audit(c,project_id,tid,"TASK_CREATED","PASS",{"title":title.strip(),"revision":1})
        return self.get_task(tid)

    def get_task(self,tid):
        with self._conn() as c:
            r=c.execute("SELECT * FROM tasks WHERE task_id=?",(tid,)).fetchone()
            if not r: raise ControlPlaneError("TASK_NOT_FOUND")
            d=dict(r); d["plan"]=json.loads(d.pop("plan_json")); d["approved"]=bool(d["approved"])
            return d

    def add_evidence(self,tid,*,source_url,retrieved_at,content,status,claim):
        if status not in EVIDENCE_STATUSES: raise ControlPlaneError("INVALID_EVIDENCE_STATUS")
        if not all(isinstance(x,str) and x.strip() for x in (source_url,retrieved_at,content,claim)): raise ControlPlaneError("EVIDENCE_FIELDS_REQUIRED")
        eid,digest,t=str(uuid.uuid4()),hashlib.sha256(content.encode()).hexdigest(),now()
        with self._tx() as c:
            task=c.execute("SELECT project_id,status FROM tasks WHERE task_id=?",(tid,)).fetchone()
            if not task: raise ControlPlaneError("TASK_NOT_FOUND")
            if task["status"] in {"COMPLETED","FAILED"}: raise ControlPlaneError("TASK_TERMINAL")
            c.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?,?,?)",(eid,tid,source_url.strip(),retrieved_at.strip(),digest,status,claim.strip(),t))
            self._audit(c,task["project_id"],tid,"EVIDENCE_ADDED", "PASS" if status=="VERIFIED" else status,
                        {"evidence_id":eid,"source_url":source_url,"content_sha256":digest,"status":status,"claim":claim})
        return {"evidence_id":eid,"task_id":tid,"source_url":source_url.strip(),"retrieved_at":retrieved_at.strip(),"content_sha256":digest,"status":status,"claim":claim.strip()}

    def set_plan(self,tid,plan):
        if not isinstance(plan,list) or not plan or any(not isinstance(x,dict) for x in plan): raise ControlPlaneError("NONEMPTY_PLAN_REQUIRED")
        with self._tx() as c:
            t=c.execute("SELECT project_id,status,revision FROM tasks WHERE task_id=?",(tid,)).fetchone()
            if not t: raise ControlPlaneError("TASK_NOT_FOUND")
            if t["status"] not in {"RECEIVED","ANALYZING","EVIDENCE_READY","PLAN_READY","BLOCKED"}: raise ControlPlaneError("PLAN_CHANGE_NOT_ALLOWED_IN_CURRENT_STATE")
            if c.execute("SELECT COUNT(*) FROM evidence WHERE task_id=? AND status='VERIFIED'",(tid,)).fetchone()[0]<1: raise ControlPlaneError("VERIFIED_EVIDENCE_REQUIRED")
            rev=t["revision"]+1
            c.execute("UPDATE tasks SET status='PLAN_READY',plan_json=?,revision=?,updated_at=? WHERE task_id=?",(js(plan),rev,now(),tid))
            self._audit(c,t["project_id"],tid,"PLAN_SET","PASS",{"revision":rev,"step_count":len(plan)})
        return self.get_task(tid)

    def approve_task(self,tid,*,actor,approved):
        if not isinstance(actor,str) or not actor.strip(): raise ControlPlaneError("APPROVAL_ACTOR_REQUIRED")
        with self._tx() as c:
            t=c.execute("SELECT project_id,status,revision FROM tasks WHERE task_id=?",(tid,)).fetchone()
            if not t: raise ControlPlaneError("TASK_NOT_FOUND")
            if t["status"]!="PLAN_READY": raise ControlPlaneError("PLAN_MUST_BE_READY_BEFORE_APPROVAL")
            if approved and c.execute("SELECT COUNT(*) FROM evidence WHERE task_id=? AND status='VERIFIED'",(tid,)).fetchone()[0]<1: raise ControlPlaneError("VERIFIED_EVIDENCE_REQUIRED")
            status="AUTHORIZED" if approved else "BLOCKED"; rev=t["revision"]+1
            c.execute("UPDATE tasks SET approved=?,status=?,revision=?,updated_at=? WHERE task_id=?",(int(bool(approved)),status,rev,now(),tid))
            self._audit(c,t["project_id"],tid,"APPROVAL_DECISION",status,{"actor":actor,"approved":bool(approved),"revision":rev})
        return self.get_task(tid)

    def authorize_execution(self,tid,*,adapter_name,permission_granted,idempotency_key):
        if not adapter_name.strip() or not idempotency_key.strip(): raise ControlPlaneError("ADAPTER_AND_IDEMPOTENCY_KEY_REQUIRED")
        req={"task_id":tid,"adapter_name":adapter_name,"permission_granted":bool(permission_granted)}
        digest=hashlib.sha256(js(req).encode()).hexdigest(); denied=False; result=None
        with self._tx() as c:
            cached=c.execute("SELECT operation,request_sha256,result_json FROM idempotency WHERE idempotency_key=?",(idempotency_key,)).fetchone()
            if cached:
                if cached["operation"]!="authorize_execution" or cached["request_sha256"]!=digest: raise ControlPlaneError("IDEMPOTENCY_KEY_REUSE_MISMATCH")
                return json.loads(cached["result_json"])
            t=c.execute("SELECT project_id,status,approved,revision FROM tasks WHERE task_id=?",(tid,)).fetchone()
            if not t: raise ControlPlaneError("TASK_NOT_FOUND")
            if t["status"]!="AUTHORIZED" or not t["approved"]: raise ControlPlaneError("EXECUTION_NOT_AUTHORIZED")
            if not permission_granted:
                self._audit(c,t["project_id"],tid,"EXECUTION_DENIED","BLOCKED",{"adapter_name":adapter_name}); denied=True
            else:
                if c.execute("SELECT COUNT(*) FROM evidence WHERE task_id=? AND status='VERIFIED'",(tid,)).fetchone()[0]<1: raise ControlPlaneError("VERIFIED_EVIDENCE_REQUIRED")
                rev=t["revision"]+1
                c.execute("UPDATE tasks SET status='EXECUTING',revision=?,updated_at=? WHERE task_id=?",(rev,now(),tid))
                result={"task_id":tid,"status":"AUTHORIZED_FOR_ADAPTER","adapter_name":adapter_name,"invocation_performed":False,"revision":rev}
                self._audit(c,t["project_id"],tid,"EXECUTION_AUTHORIZED","PASS",result)
                c.execute("INSERT INTO idempotency VALUES(?,?,?,?,?)",(idempotency_key,"authorize_execution",digest,js(result),now()))
        if denied: raise ControlPlaneError("ADAPTER_PERMISSION_DENIED")
        return result

    def record_execution_result(self,tid,*,adapter_name,outcome,evidence_ref=None):
        if outcome not in {"SUCCEEDED","FAILED","UNKNOWN_OUTCOME"}: raise ControlPlaneError("INVALID_EXECUTION_OUTCOME")
        with self._tx() as c:
            t=c.execute("SELECT project_id,status,revision FROM tasks WHERE task_id=?",(tid,)).fetchone()
            if not t: raise ControlPlaneError("TASK_NOT_FOUND")
            if t["status"]!="EXECUTING": raise ControlPlaneError("TASK_NOT_EXECUTING")
            status={"SUCCEEDED":"VERIFYING","FAILED":"FAILED","UNKNOWN_OUTCOME":"BLOCKED"}[outcome]; rev=t["revision"]+1
            c.execute("UPDATE tasks SET status=?,revision=?,updated_at=? WHERE task_id=?",(status,rev,now(),tid))
            result={"task_id":tid,"adapter_name":adapter_name,"outcome":outcome,"status":status,"evidence_ref":evidence_ref}
            self._audit(c,t["project_id"],tid,"EXECUTION_RESULT",status,result)
        return result

    def verify_task(self,tid,*,passed,verification_ref):
        if not isinstance(verification_ref,str) or not verification_ref.strip(): raise ControlPlaneError("VERIFICATION_REFERENCE_REQUIRED")
        with self._tx() as c:
            t=c.execute("SELECT project_id,status,revision FROM tasks WHERE task_id=?",(tid,)).fetchone()
            if not t: raise ControlPlaneError("TASK_NOT_FOUND")
            if t["status"]!="VERIFYING": raise ControlPlaneError("TASK_NOT_READY_FOR_VERIFICATION")
            status="COMPLETED" if passed else "BLOCKED"; rev=t["revision"]+1
            c.execute("UPDATE tasks SET status=?,revision=?,updated_at=? WHERE task_id=?",(status,rev,now(),tid))
            self._audit(c,t["project_id"],tid,"FINAL_VERIFICATION","PASS" if passed else "BLOCKED",{"passed":bool(passed),"verification_ref":verification_ref,"status":status})
        return self.get_task(tid)

    def checkpoint(self,tid):
        with self._tx() as c:
            t=c.execute("SELECT * FROM tasks WHERE task_id=?",(tid,)).fetchone()
            if not t: raise ControlPlaneError("TASK_NOT_FOUND")
            td=dict(t); td["plan"]=json.loads(td.pop("plan_json"))
            ev=[dict(r) for r in c.execute("SELECT * FROM evidence WHERE task_id=? ORDER BY created_at",(tid,)).fetchall()]
            snap={"task":td,"evidence":ev,"captured_at":now()}; cid=str(uuid.uuid4())
            c.execute("INSERT INTO checkpoints VALUES(?,?,?,?,?)",(cid,tid,t["revision"],js(snap),snap["captured_at"]))
            self._audit(c,t["project_id"],tid,"CHECKPOINT_CREATED","PASS",{"checkpoint_id":cid,"revision":t["revision"]})
        return {"checkpoint_id":cid,"task_id":tid,"revision":t["revision"],"snapshot":snap}

    def restore_checkpoint(self,tid,checkpoint_id,*,actor):
        if not isinstance(actor,str) or not actor.strip(): raise ControlPlaneError("RECOVERY_ACTOR_REQUIRED")
        with self._tx() as c:
            t=c.execute("SELECT * FROM tasks WHERE task_id=?",(tid,)).fetchone()
            if not t: raise ControlPlaneError("TASK_NOT_FOUND")
            if t["status"] not in {"BLOCKED","FAILED"}: raise ControlPlaneError("TASK_NOT_RECOVERABLE_FROM_CURRENT_STATE")
            cp=c.execute("SELECT * FROM checkpoints WHERE checkpoint_id=? AND task_id=?",(checkpoint_id,tid)).fetchone()
            if not cp: raise ControlPlaneError("CHECKPOINT_NOT_FOUND_FOR_TASK")
            snap=json.loads(cp["snapshot_json"]); plan=snap.get("task",{}).get("plan",[])
            verified=c.execute("SELECT COUNT(*) FROM evidence WHERE task_id=? AND status='VERIFIED'",(tid,)).fetchone()[0]
            status="PLAN_READY" if plan and verified else "RECEIVED"; rev=t["revision"]+1
            c.execute("UPDATE tasks SET status=?,approved=0,plan_json=?,revision=?,updated_at=? WHERE task_id=?",(status,js(plan if status=="PLAN_READY" else []),rev,now(),tid))
            self._audit(c,t["project_id"],tid,"CHECKPOINT_RESTORED","PASS",{"checkpoint_id":checkpoint_id,"actor":actor,"from_revision":t["revision"],"restored_revision":rev,"restored_status":status,"approval_reset":True,"in_flight_side_effect_replayed":False})
        return self.get_task(tid)


    def start_agent_action(self, *, session_id, trace_id, actor_id, action_name, task_id=None, inputs=None):
        """Append a durable STARTED event before an MCP tool action is executed."""
        for key, value in (("session_id", session_id), ("trace_id", trace_id),
                           ("actor_id", actor_id), ("action_name", action_name)):
            if not isinstance(value, str) or not value.strip():
                raise ControlPlaneError(f"AGENT_ACTION_{key.upper()}_REQUIRED")
        action_id = str(uuid.uuid4())
        project_id = None
        with self._tx() as c:
            if task_id:
                row = c.execute("SELECT project_id FROM tasks WHERE task_id=?", (task_id,)).fetchone()
                if row:
                    project_id = row["project_id"]
            c.execute(
                "INSERT INTO agent_action_events(action_id,session_id,trace_id,project_id,task_id,actor_id,action_name,occurred_at,phase,status,payload_json) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (action_id, session_id, trace_id, project_id, task_id, actor_id, action_name,
                 now(), "STARTED", "IN_PROGRESS", js(redact(inputs or {}))))
        return {"action_id": action_id, "session_id": session_id, "trace_id": trace_id,
                "task_id": task_id, "action_name": action_name, "status": "IN_PROGRESS"}

    def finish_agent_action(self, action_id, *, status, outputs=None, error_type=None, error_message=None):
        """Append a terminal event; never rewrite the STARTED record."""
        allowed = {"SUCCEEDED", "FAILED", "BLOCKED", "UNKNOWN_OUTCOME"}
        if status not in allowed:
            raise ControlPlaneError("AGENT_ACTION_STATUS_INVALID")
        with self._tx() as c:
            started = c.execute(
                "SELECT * FROM agent_action_events WHERE action_id=? AND phase='STARTED' ORDER BY event_id LIMIT 1",
                (action_id,)).fetchone()
            if not started:
                raise ControlPlaneError("AGENT_ACTION_NOT_FOUND")
            if c.execute("SELECT COUNT(*) FROM agent_action_events WHERE action_id=? AND phase='FINISHED'",
                          (action_id,)).fetchone()[0]:
                raise ControlPlaneError("AGENT_ACTION_ALREADY_FINISHED")
            payload = {"outputs": redact(outputs or {}), "error_type": error_type,
                       "error_message": redact(error_message) if error_message else None}
            c.execute(
                "INSERT INTO agent_action_events(action_id,session_id,trace_id,project_id,task_id,actor_id,action_name,occurred_at,phase,status,payload_json) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (action_id, started["session_id"], started["trace_id"], started["project_id"],
                 started["task_id"], started["actor_id"], started["action_name"], now(),
                 "FINISHED", status, js(payload)))
        return {"action_id": action_id, "status": status}

    def get_agent_actions(self, *, task_id=None, session_id=None, limit=100):
        if not isinstance(limit, int) or limit < 1 or limit > 500:
            raise ControlPlaneError("AGENT_ACTION_LIMIT_OUT_OF_RANGE")
        if not task_id and not session_id:
            raise ControlPlaneError("TASK_OR_SESSION_REQUIRED")
        clauses, params = [], []
        if task_id:
            clauses.append("task_id=?")
            params.append(task_id)
        if session_id:
            clauses.append("session_id=?")
            params.append(session_id)
        params.append(limit)
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM agent_action_events WHERE " + " AND ".join(clauses) +
                " ORDER BY event_id DESC LIMIT ?", params).fetchall()
            return [{**dict(row), "payload": json.loads(row["payload_json"])}
                    for row in reversed(rows)]

    def get_resume_context(self, task_id):
        """Return evidence-backed state and recent recorded actions; do not infer missing history."""
        task = self.get_task(task_id)
        actions = self.get_agent_actions(task_id=task_id, limit=100)
        audit = self.get_audit(task_id)
        with self._conn() as c:
            cp = c.execute(
                "SELECT checkpoint_id,revision,created_at FROM checkpoints WHERE task_id=? ORDER BY created_at DESC LIMIT 1",
                (task_id,)).fetchone()
        return {"status": "RECOVERED" if actions or audit or cp else "UNKNOWN",
                "task": task, "latest_checkpoint": dict(cp) if cp else None,
                "recent_agent_actions": actions, "audit_events": audit,
                "history_limit": 100,
                "limitations": ["Only actions routed through the IRIS MCP adapter are captured.",
                                "This journal does not capture hidden model reasoning or actions outside this adapter."]}

    def get_audit(self,tid):
        with self._conn() as c:
            return [{**dict(r),"payload":json.loads(r["payload_json"])} for r in c.execute("SELECT * FROM audit_events WHERE task_id=? ORDER BY event_id",(tid,)).fetchall()]

    def get_evidence(self,tid):
        with self._conn() as c:
            return [dict(r) for r in c.execute("SELECT * FROM evidence WHERE task_id=? ORDER BY created_at",(tid,)).fetchall()]
