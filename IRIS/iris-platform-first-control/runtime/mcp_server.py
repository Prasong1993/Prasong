"""MCP adapter. Keep write-capable endpoints local until transport authentication is configured."""
from __future__ import annotations
import inspect, json, os, uuid
from pathlib import Path
from typing import Any
from mcp.server import MCPServer
from runtime.control_plane import ControlPlaneError
from runtime.verified_control_plane import VerifiedControlPlane
from runtime.source_verifier import SourceVerifier

DB_PATH = os.environ.get("IRIS_DB_PATH", str(Path(__file__).resolve().parents[1] / "data" / "iris.sqlite3"))
control = VerifiedControlPlane(DB_PATH)
source_verifier = SourceVerifier(control)
MCP_SESSION_ID = str(uuid.uuid4())  # process session, not a verified ChatGPT conversation ID
MCP_ACTOR_ID = "mcp-caller-unverified"  # caller identity is not authenticated by this local stdio adapter
mcp = MCPServer("IRIS Platform-First Control")

def _journal_projection(value: Any, *, depth: int = 0) -> Any:
    """Bound journal payloads; retain useful metadata, not arbitrary result bodies."""
    if depth >= 4:
        return "[TRUNCATED_DEPTH]"
    if isinstance(value, dict):
        items = list(value.items())[:30]
        projected = {str(k): _journal_projection(v, depth=depth + 1) for k, v in items}
        if len(value) > len(items):
            projected["_truncated_keys"] = len(value) - len(items)
        return projected
    if isinstance(value, (list, tuple)):
        return {
            "_kind": "list",
            "item_count": len(value),
            "sample": [_journal_projection(v, depth=depth + 1) for v in value[:10]],
            "truncated": len(value) > 10,
        }
    if isinstance(value, str):
        return value[:500] + ("...[TRUNCATED]" if len(value) > 500 else "")
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return f"<{type(value).__name__}>"

def _journal_result_projection(action_name: str, result: Any) -> Any:
    # History-reading tools must not journal their entire history back into itself.
    if action_name == "get_agent_actions" and isinstance(result, list):
        return {"kind": "action_history", "item_count": len(result),
                "action_ids": [x.get("action_id") for x in result[:20] if isinstance(x, dict)]}
    if action_name == "get_resume_context" and isinstance(result, dict):
        actions = result.get("recent_agent_actions", [])
        return {"kind": "resume_context", "task_id": (result.get("task") or {}).get("task_id")
                if isinstance(result.get("task"), dict) else None,
                "action_count": len(actions) if isinstance(actions, list) else None,
                "checkpoint_present": bool(result.get("latest_checkpoint")),
                "audit_event_count": len(result.get("audit_events", []))
                if isinstance(result.get("audit_events"), list) else None}
    if action_name in {"get_audit", "get_evidence"} and isinstance(result, list):
        return {"kind": action_name, "item_count": len(result)}
    return _journal_projection(result)

def safe(fn):
    """Journal each observable MCP tool invocation before and after execution."""
    frame = inspect.currentframe()
    caller = frame.f_back if frame else None
    action_name = caller.f_code.co_name if caller else "unknown_tool"
    local_values = {}
    task_id = None
    if caller:
        task_id = caller.f_locals.get("task_id")
        for key, value in caller.f_locals.items():
            if key in {"fn", "run", "self"} or key.startswith("_"):
                continue
            if isinstance(value, (str, int, float, bool, type(None), list, dict)):
                local_values[key] = value
    trace_id = str(uuid.uuid4())
    try:
        started = control.start_agent_action(
            session_id=MCP_SESSION_ID, trace_id=trace_id,
            actor_id=MCP_ACTOR_ID, action_name=action_name,
            task_id=task_id, inputs=_journal_projection(local_values))
    except Exception:
        return {"status":"BLOCKED","error_type":"ACTION_JOURNAL_UNAVAILABLE",
                "message":"The action was not executed because its start record could not be persisted.",
                "trace_id":trace_id}
    try:
        result = fn()
    except ControlPlaneError as exc:
        try:
            control.finish_agent_action(started["action_id"], status="BLOCKED",
                outputs={"status":"ERROR"}, error_type="CONTROL_PLANE_POLICY",
                error_message=str(exc))
        except Exception:
            return {"status":"UNKNOWN_OUTCOME","error_type":"ACTION_JOURNAL_FINISH_FAILED",
                    "trace_id":trace_id,"message":"The operation failed and its final journal event could not be persisted; inspect state before retrying."}
        return {"status":"ERROR","error_type":"CONTROL_PLANE_POLICY","message":str(exc),
                "action_id":started["action_id"],"trace_id":trace_id}
    except Exception:
        try:
            control.finish_agent_action(started["action_id"], status="FAILED",
                outputs={"status":"ERROR"}, error_type="INTERNAL_ERROR",
                error_message="An internal control-plane error occurred.")
        except Exception:
            return {"status":"UNKNOWN_OUTCOME","error_type":"ACTION_JOURNAL_FINISH_FAILED",
                    "trace_id":trace_id,"message":"The operation outcome may be unknown; inspect state before retrying."}
        return {"status":"ERROR","error_type":"INTERNAL_ERROR",
                "message":"An internal control-plane error occurred.",
                "action_id":started["action_id"],"trace_id":trace_id}
    try:
        control.finish_agent_action(started["action_id"], status="SUCCEEDED",
            outputs=_journal_result_projection(action_name, result))
    except Exception:
        return {"status":"UNKNOWN_OUTCOME","error_type":"ACTION_JOURNAL_FINISH_FAILED",
                "trace_id":trace_id,"message":"The operation may have completed but its final journal event could not be persisted; inspect state before retrying."}
    if isinstance(result, dict):
        result = dict(result)
        result.setdefault("action_id", started["action_id"])
        result.setdefault("trace_id", trace_id)
    return result

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
def add_evidence(task_id: str, source_url: str, claim: str) -> dict[str, Any]:
    """Fetch an allowlisted HTTPS source and record its digest; this verifies source retrieval, not claim truth."""
    return safe(lambda: source_verifier.ingest(task_id, source_url=source_url, claim=claim))

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

@mcp.tool()
def get_agent_actions(task_id: str = "", session_id: str = "", limit: int = 100) -> list[dict[str, Any]]:
    """Read the append-only record of observable IRIS MCP tool actions by task or process session."""
    return safe(lambda: control.get_agent_actions(
        task_id=task_id or None, session_id=session_id or None, limit=limit))

@mcp.tool()
def get_resume_context(task_id: str) -> dict[str, Any]:
    """Recover task state, latest checkpoint metadata, audit, and recorded MCP actions for continuation."""
    return safe(lambda: control.get_resume_context(task_id))
