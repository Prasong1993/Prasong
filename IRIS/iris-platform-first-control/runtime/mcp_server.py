"""MCP adapter. Keep write-capable endpoints local until transport authentication is configured."""
from __future__ import annotations
import json, os
from pathlib import Path
from typing import Any
from mcp.server import MCPServer
from runtime.control_plane import ControlPlaneError
from runtime.verified_control_plane import VerifiedControlPlane

DB_PATH = os.environ.get("IRIS_DB_PATH", str(Path(__file__).resolve().parents[1] / "data" / "iris.sqlite3"))
control = VerifiedControlPlane(DB_PATH)
mcp = MCPServer("IRIS Platform-First Control")

def safe(fn):
    try:
        return fn()
    except ControlPlaneError as exc:
        return {"status":"ERROR","error_type":"CONTROL_PLANE_POLICY","message":str(exc)}
    except Exception:
        return {"status":"ERROR","error_type":"INTERNAL_ERROR","message":"An internal control-plane error occurred."}

@mcp.tool()
def health() -> dict[str, Any]:
    """Check control database health."""
    return safe(control.health)

@mcp.tool()
def create_project(name: str) -> dict[str, Any]:
    """Create a project and audit event."""
    return safe(lambda: control.create_project(name))

@mcp.tool()
def create_task(project_id: str, title: str) -> dict[str, Any]:
    """Create a task in an active project."""
    return safe(lambda: control.create_task(project_id, title))

@mcp.tool()
def get_task(task_id: str) -> dict[str, Any]:
    """Read task state and revision."""
    return safe(lambda: control.get_task(task_id))

@mcp.tool()
def add_evidence(task_id: str, source_url: str, retrieved_at: str, content: str, claim: str) -> dict[str, Any]:
    """Record incoming evidence as UNKNOWN; only a trusted server-side verifier may mark it VERIFIED."""
    return safe(lambda: control.add_evidence(task_id, source_url=source_url, retrieved_at=retrieved_at,
                                             content=content, status="UNKNOWN", claim=claim))

@mcp.tool()
def set_plan(task_id: str, plan_json: str) -> dict[str, Any]:
    """Set a JSON-array plan; trusted VERIFIED evidence is required."""
    def run():
        try:
            plan = json.loads(plan_json)
        except (TypeError, json.JSONDecodeError):
            raise ControlPlaneError("PLAN_JSON_INVALID")
        return control.set_plan(task_id, plan)
    return safe(run)

@mcp.tool()
def approve_task(task_id: str, actor: str, approved: bool) -> dict[str, Any]:
    """Record an explicit approval decision; this does not execute tools."""
    return safe(lambda: control.approve_task(task_id, actor=actor, approved=approved))

@mcp.tool()
def authorize_execution(task_id: str, adapter_name: str, permission_granted: bool, idempotency_key: str) -> dict[str, Any]:
    """Authorize a host adapter after gates; never invokes that adapter."""
    return safe(lambda: control.authorize_execution(task_id, adapter_name=adapter_name,
        permission_granted=permission_granted, idempotency_key=idempotency_key))

@mcp.tool()
def record_execution_result(task_id: str, adapter_name: str, outcome: str, evidence_ref: str = "") -> dict[str, Any]:
    """Record a real adapter result; UNKNOWN_OUTCOME blocks further execution."""
    return safe(lambda: control.record_execution_result(task_id, adapter_name=adapter_name,
        outcome=outcome, evidence_ref=evidence_ref or None))

@mcp.tool()
def verify_task(task_id: str, passed: bool, verification_ref: str) -> dict[str, Any]:
    """Complete only after a verification reference is supplied."""
    return safe(lambda: control.verify_task(task_id, passed=passed, verification_ref=verification_ref))

@mcp.tool()
def checkpoint(task_id: str) -> dict[str, Any]:
    """Persist a task checkpoint for recovery."""
    return safe(lambda: control.checkpoint(task_id))

@mcp.tool()
def restore_checkpoint(task_id: str, checkpoint_id: str, actor: str) -> dict[str, Any]:
    """Restore planning state from BLOCKED/FAILED; reset approval and never replay side effects."""
    return safe(lambda: control.restore_checkpoint(task_id, checkpoint_id, actor=actor))

@mcp.tool()
def get_evidence(task_id: str) -> list[dict[str, Any]]:
    """Read task evidence metadata."""
    return safe(lambda: control.get_evidence(task_id))

@mcp.tool()
def get_audit(task_id: str) -> list[dict[str, Any]]:
    """Read the append-only audit trail."""
    return safe(lambda: control.get_audit(task_id))
