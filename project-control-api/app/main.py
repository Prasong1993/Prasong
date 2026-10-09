from __future__ import annotations
import os
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.core import ProjectControl, ControlError

app = FastAPI(title="Project Control API", version="1.0.0", description="Deterministic workflow gates, evidence hashes, and tamper-evident audit trail.")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "*").split(","), allow_credentials=False, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type", "X-Project-Control-Key"])
controller = ProjectControl(os.getenv("PROJECT_CONTROL_DB", "data/project_control.db"))

class ControlRequest(BaseModel):
    action: str
    title: str | None = None
    description: str = ""
    runId: str | None = None
    source: str | None = None
    content: str | None = None

@app.get("/_api/health")
def health():
    return {"status": "ok", "service": "Project Control API", "version": "1.0.0", "deterministicGates": True}

@app.post("/_api/control")
def control(body: ControlRequest, x_project_control_key: str | None = Header(default=None, alias="X-Project-Control-Key")):
    expected = os.getenv("PROJECT_CONTROL_KEY")
    if not expected or x_project_control_key is None or x_project_control_key != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        if body.action == "list": return {"runs": controller.list_runs()}
        if body.action == "create":
            if body.title is None: raise ControlError("title required", 400)
            return controller.create(body.title, body.description)
        if not body.runId: raise ControlError("runId required", 400)
        if body.action == "detail": return controller.detail(body.runId)
        if body.action == "evidence":
            if body.source is None or body.content is None: raise ControlError("source and content required", 400)
            return controller.add_evidence(body.runId, body.source, body.content)
        if body.action == "advance": return controller.advance(body.runId)
        if body.action == "verify": return controller.verify(body.runId)
        if body.action == "audit": return controller.audit(body.runId)
        raise ControlError("Unknown action", 400, allowed=["list", "create", "detail", "evidence", "advance", "verify", "audit"])
    except ControlError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"error": exc.message, **exc.details}) from exc
