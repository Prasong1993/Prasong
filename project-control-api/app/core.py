"""Deterministic project workflow and audit core. No LLM calls in policy or verification."""
from __future__ import annotations
import hashlib, json, sqlite3, uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGES = ("CONCEPT", "DESIGN", "EXECUTE", "RESULT", "VERIFY")
GENESIS = "GENESIS"

def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

class ControlError(Exception):
    def __init__(self, message: str, status_code: int = 400, **details: Any):
        super().__init__(message)
        self.message, self.status_code, self.details = message, status_code, details

class ProjectControl:
    def __init__(self, db_path: str | Path = "data/project_control.db"):
        self.db_path = str(db_path)
        if self.db_path != ":memory:": Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.db_path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        try:
            with db: yield db
        finally: db.close()

    def _init_db(self):
        with self._connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY,title TEXT NOT NULL,description TEXT NOT NULL DEFAULT '',status TEXT NOT NULL CHECK(status IN ('ACTIVE','COMPLETE')),current_stage TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS evidence (id TEXT PRIMARY KEY,run_id TEXT NOT NULL REFERENCES runs(id),stage TEXT NOT NULL,source TEXT NOT NULL,content TEXT NOT NULL,content_hash TEXT NOT NULL,created_at TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS evidence_run_stage_idx ON evidence(run_id,stage);
            CREATE TABLE IF NOT EXISTS audit_log (seq INTEGER PRIMARY KEY AUTOINCREMENT,id TEXT NOT NULL UNIQUE,run_id TEXT NOT NULL REFERENCES runs(id),event_type TEXT NOT NULL,payload TEXT NOT NULL,prev_hash TEXT NOT NULL,event_hash TEXT NOT NULL,created_at TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS audit_run_seq_idx ON audit_log(run_id,seq);
            """)

    def _audit(self, db, run_id: str, event_type: str, payload: dict):
        last = db.execute("SELECT event_hash FROM audit_log WHERE run_id=? ORDER BY seq DESC LIMIT 1", (run_id,)).fetchone()
        event_id, created_at = str(uuid.uuid4()), now()
        payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        prev_hash = last["event_hash"] if last else GENESIS
        event_hash = sha256("|".join((event_id, run_id, event_type, payload_json, prev_hash, created_at)))
        db.execute("INSERT INTO audit_log(id,run_id,event_type,payload,prev_hash,event_hash,created_at) VALUES(?,?,?,?,?,?,?)", (event_id,run_id,event_type,payload_json,prev_hash,event_hash,created_at))

    def create(self, title: str, description: str = "") -> dict:
        if not isinstance(title,str) or not title.strip(): raise ControlError("title required",400)
        run_id, stamp = str(uuid.uuid4()), now()
        with self._connect() as db:
            db.execute("INSERT INTO runs VALUES(?,?,?,?,?,?,?)",(run_id,title.strip(),description or "","ACTIVE",STAGES[0],stamp,stamp))
            self._audit(db,run_id,"RUN_CREATED",{"title":title.strip()})
        return self.detail(run_id)["run"]

    def list_runs(self) -> list[dict]:
        with self._connect() as db: return [dict(r) for r in db.execute("SELECT * FROM runs ORDER BY created_at DESC")]

    def _get_run(self, db, run_id: str):
        run=db.execute("SELECT * FROM runs WHERE id=?",(run_id,)).fetchone()
        if not run: raise ControlError("Run not found",404)
        return run

    def detail(self, run_id: str) -> dict:
        with self._connect() as db:
            run=self._get_run(db,run_id)
            evidence=[dict(e) for e in db.execute("SELECT id,stage,source,content,content_hash,created_at FROM evidence WHERE run_id=? ORDER BY rowid",(run_id,))]
            return {"run":dict(run),"evidence":evidence}

    def add_evidence(self, run_id: str, source: str, content: str) -> dict:
        if not isinstance(source,str) or not source.strip() or not isinstance(content,str) or not content.strip(): raise ControlError("non-empty source and content required",400)
        with self._connect() as db:
            run=self._get_run(db,run_id)
            if run["status"]=="COMPLETE": raise ControlError("Completed run is immutable",409)
            evidence_id,stamp=str(uuid.uuid4()),now(); content_hash=sha256(content); stage=run["current_stage"]
            db.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?,?)",(evidence_id,run_id,stage,source.strip(),content,content_hash,stamp))
            db.execute("UPDATE runs SET updated_at=? WHERE id=?",(stamp,run_id))
            self._audit(db,run_id,"EVIDENCE_ADDED",{"id":evidence_id,"stage":stage,"source":source.strip(),"content_hash":content_hash})
            return {"id":evidence_id,"run_id":run_id,"stage":stage,"source":source.strip(),"content_hash":content_hash,"created_at":stamp}

    def advance(self, run_id: str) -> dict:
        with self._connect() as db:
            run=self._get_run(db,run_id)
            if run["status"]=="COMPLETE": raise ControlError("Completed run is immutable",409)
            stage=run["current_stage"]
            if stage not in STAGES or STAGES.index(stage)>=len(STAGES)-1: raise ControlError("Cannot advance further",409,stage=stage)
            count=db.execute("SELECT COUNT(*) FROM evidence WHERE run_id=? AND stage=?",(run_id,stage)).fetchone()[0]
            if not count: raise ControlError("Evidence required before advancing",409,stage=stage)
            next_stage,stamp=STAGES[STAGES.index(stage)+1],now()
            db.execute("UPDATE runs SET current_stage=?,updated_at=? WHERE id=?",(next_stage,stamp,run_id))
            self._audit(db,run_id,"STAGE_ADVANCED",{"from":stage,"to":next_stage})
            return {"run_id":run_id,"previous_stage":stage,"current_stage":next_stage}

    def _verify_integrity(self, db, run_id: str) -> dict:
        events=[dict(r) for r in db.execute("SELECT * FROM audit_log WHERE run_id=? ORDER BY seq",(run_id,))]
        if not events: return {"ok":False,"reason":"empty_audit","events":0}
        previous=GENESIS; logged_evidence=set(); replay_stage,completed_events=STAGES[0],0
        for index,event in enumerate(events):
            expected=sha256("|".join((event["id"],run_id,event["event_type"],event["payload"],previous,event["created_at"])))
            if event["prev_hash"]!=previous or event["event_hash"]!=expected: return {"ok":False,"reason":"audit_hash_mismatch","event_id":event["id"],"events":len(events)}
            try: payload=json.loads(event["payload"])
            except json.JSONDecodeError: return {"ok":False,"reason":"invalid_audit_payload","events":len(events)}
            if event["event_type"]=="RUN_CREATED":
                if index!=0: return {"ok":False,"reason":"run_created_not_first","events":len(events)}
            elif event["event_type"]=="EVIDENCE_ADDED":
                logged_evidence.add(payload.get("id"))
                if payload.get("stage")!=replay_stage: return {"ok":False,"reason":"evidence_stage_mismatch","events":len(events)}
            elif event["event_type"]=="STAGE_ADVANCED":
                idx=STAGES.index(replay_stage)
                if idx>=len(STAGES)-1 or payload.get("from")!=replay_stage or payload.get("to")!=STAGES[idx+1]: return {"ok":False,"reason":"illegal_stage_transition","events":len(events)}
                replay_stage=STAGES[idx+1]
            elif event["event_type"]=="RUN_COMPLETED":
                completed_events+=1
                if replay_stage!="VERIFY" or payload.get("stages")!=list(STAGES): return {"ok":False,"reason":"invalid_completion_event","events":len(events)}
            else: return {"ok":False,"reason":"unknown_event_type","events":len(events)}
            previous=event["event_hash"]
        evidence_rows=[dict(e) for e in db.execute("SELECT * FROM evidence WHERE run_id=?",(run_id,))]
        if {e["id"] for e in evidence_rows}!=logged_evidence: return {"ok":False,"reason":"evidence_log_mismatch","events":len(events)}
        for evidence in evidence_rows:
            if sha256(evidence["content"])!=evidence["content_hash"]: return {"ok":False,"reason":"evidence_content_hash_mismatch","evidence_id":evidence["id"],"events":len(events)}
            logged=next((json.loads(x["payload"]) for x in events if x["event_type"]=="EVIDENCE_ADDED" and json.loads(x["payload"]).get("id")==evidence["id"]),None)
            if not logged or any(logged.get(k)!=evidence[v] for k,v in (("stage","stage"),("source","source"),("content_hash","content_hash"))): return {"ok":False,"reason":"evidence_metadata_mismatch","evidence_id":evidence["id"],"events":len(events)}
        run=self._get_run(db,run_id)
        if run["current_stage"]!=replay_stage: return {"ok":False,"reason":"run_stage_mismatch","events":len(events)}
        if run["status"]=="COMPLETE":
            if completed_events!=1 or events[-1]["event_type"]!="RUN_COMPLETED": return {"ok":False,"reason":"completion_event_mismatch","events":len(events)}
        elif completed_events: return {"ok":False,"reason":"premature_completion_event","events":len(events)}
        return {"ok":True,"events":len(events),"evidence":len(evidence_rows),"replayed_stage":replay_stage}

    def verify(self, run_id: str) -> dict:
        with self._connect() as db:
            run=self._get_run(db,run_id)
            if run["status"]=="COMPLETE":
                integrity=self._verify_integrity(db,run_id)
                if not integrity["ok"]: raise ControlError("Integrity check failed",409,integrity=integrity)
                return {"run_id":run_id,"status":"COMPLETE","already_complete":True,"integrity":integrity}
            if run["current_stage"]!="VERIFY": raise ControlError("Run must reach VERIFY stage",409,current_stage=run["current_stage"])
            for stage in STAGES:
                if db.execute("SELECT COUNT(*) FROM evidence WHERE run_id=? AND stage=?",(run_id,stage)).fetchone()[0]==0: raise ControlError("Evidence missing",409,stage=stage)
            integrity=self._verify_integrity(db,run_id)
            if not integrity["ok"]: raise ControlError("Integrity check failed",409,integrity=integrity)
            stamp=now(); db.execute("UPDATE runs SET status='COMPLETE',updated_at=? WHERE id=?",(stamp,run_id))
            self._audit(db,run_id,"RUN_COMPLETED",{"stages":list(STAGES),"integrity":integrity})
            final_integrity=self._verify_integrity(db,run_id)
            if not final_integrity["ok"]: raise ControlError("Post-completion integrity check failed",500,integrity=final_integrity)
            return {"run_id":run_id,"status":"COMPLETE","integrity":final_integrity}

    def audit(self, run_id: str) -> dict:
        with self._connect() as db:
            self._get_run(db,run_id); integrity=self._verify_integrity(db,run_id)
            events=[dict(r) for r in db.execute("SELECT seq,id,event_type,payload,prev_hash,event_hash,created_at FROM audit_log WHERE run_id=? ORDER BY seq",(run_id,))]
            return {"integrity":integrity,"events":events}
