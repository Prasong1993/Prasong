"""IRIS Controller MCP Server (stdio transport).

Exposes the IRIS five-step workflow as MCP tools so any MCP-compatible
host (Codex Plugin Creator, Claude Desktop, etc.) can drive the controller
with real persistence (SQLite), gates, error capture, checkpoints, audit
and final verification.

Design rules (fixed from v0.6.x gaps):
  * Every tool returns a JSON object with a top-level "status" field:
    "OK" | "ERROR". Errors are structured (error_type, message) and never
    raised as raw Python exceptions across the MCP boundary.
  * run_step accepts real `expected` and `actual` values (not derived from
    a status flag), matching the REST controller semantics.
  * final_verify persists MISMATCH rows into `verifications` and `audit_log`
    exactly like the REST path, so failures are always retained.
  * Database path is read from IRIS_DB_PATH (fallback: runtime/data/iris.db).
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

# Ensure runtime/ is importable when launched as `python runtime/mcp_server.py`
sys.path.insert(0, str(Path(__file__).resolve().parent))

import database  # noqa: E402
from controller import create_work, run_step, get_work, record_error, checkpoint  # noqa: E402
from model import STEP_DEFINITIONS, StepStatus  # noqa: E402

from mcp.server import Server  # noqa: E402
from mcp.server.stdio import stdio_server  # noqa: E402
from mcp.types import Tool, TextContent  # noqa: E402

APP_VERSION = "0.6.5"

server = Server("iris-controller")


def _ok(payload: dict) -> list[TextContent]:
    payload = dict(payload)
    # Avoid clobbering the top-level protocol status ("OK") with a payload
    # field also named "status" (e.g. run_step returns status='PASSED').
    if "status" in payload:
        payload["result_status"] = payload.pop("status")
    payload = {"status": "OK", "version": APP_VERSION, **payload}
    return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))]


def _err(error_type: str, message: str, **extra) -> list[TextContent]:
    payload = {"status": "ERROR", "error_type": error_type, "message": message, **extra}
    return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))]


def _final_verify_persist(work_id: str, expected: str, actual: str, note: str = "") -> dict:
    """Mirror REST final_verify: gate on 5 PASS, persist result, update status."""
    result = get_work(work_id)
    if not result:
        return {"status": "ERROR", "error_type": "NOT_FOUND", "message": f"work {work_id} not found"}
    latest = {}
    for row in result["steps"]:
        latest[row["step"]] = row
    missing = [i for i in STEP_DEFINITIONS if latest.get(i, {}).get("status") != StepStatus.PASSED.value]
    if missing:
        return {"status": "ERROR", "error_type": "GATE_VIOLATION",
                "message": f"final verification requires all five steps to PASS; missing/failed: {missing}"}
    status = "VERIFIED" if str(expected).strip() == str(actual).strip() else "MISMATCH"
    with database.get_connection() as conn:
        conn.execute(
            "INSERT INTO verifications(work_id,expected,actual,status,note) VALUES(?,?,?,?,?)",
            (work_id, expected, actual, status, note),
        )
        conn.execute(
            "INSERT INTO audit_log(work_id,action,details) VALUES(?,?,?)",
            (work_id, "FINAL_VERIFICATION", f"status={status}"),
        )
        if status == "VERIFIED":
            conn.execute(
                "UPDATE work_units SET status='DELIVERED', updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (work_id,),
            )
    if status != "VERIFIED":
        # Retain the failure in errors table as well (evidence-first)
        record_error(work_id, step=0, attempt=0, error_type="FINAL_VERIFICATION_MISMATCH",
                     message="final expected vs actual mismatch; result retained as unverified",
                     expected=expected, actual=actual, root_cause="MISMATCH",
                     impact="work not delivered", correction="correct output and retry final verification",
                     verification="MISMATCH", prevention_rule="never promote mismatch to VERIFIED")
        checkpoint(work_id, step=0, state="FINAL_MISMATCH",
                   snapshot={"expected": expected, "actual": actual, "retained": True})
        return {"status": "ERROR", "error_type": "FINAL_MISMATCH",
                "message": "final verification mismatch; result retained as unverified",
                "persisted": True, "verification_status": status}
    return {"status": "OK", "verification_status": "VERIFIED", "work_id": work_id, "delivered": True}


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------
_TOOLS = [
    Tool(
        name="create_work",
        description="Create a new IRIS work unit. Returns work id and status CREATED. Duplicate id returns structured CONFLICT error.",
        inputSchema={
            "type": "object",
            "properties": {
                "work_id": {"type": "string", "description": "Unique work identifier (1-128 chars)"},
                "title": {"type": "string", "description": "Human-readable work title (1-300 chars)"},
            },
            "required": ["work_id", "title"],
        },
    ),
    Tool(
        name="run_step",
        description="Execute one gated step (1-5) with real expected vs actual verification. Step N requires step N-1 to be PASSED. Failures are retained in errors/checkpoints/audit and retried up to max_attempts.",
        inputSchema={
            "type": "object",
            "properties": {
                "work_id": {"type": "string"},
                "step": {"type": "integer", "minimum": 1, "maximum": 5},
                "expected": {"type": "string", "description": "Expected result / acceptance condition"},
                "actual": {"type": "string", "description": "Actual result produced by execution"},
                "note": {"type": "string", "description": "Optional note (max 2000 chars)"},
                "fail_attempts": {"type": "integer", "minimum": 0, "maximum": 9, "default": 0,
                                  "description": "Simulate N initial failures (for recovery testing)"},
                "max_attempts": {"type": "integer", "minimum": 1, "maximum": 10, "default": 10},
            },
            "required": ["work_id", "step", "expected", "actual"],
        },
    ),
    Tool(
        name="final_verify",
        description="Final expected-vs-actual verification. Requires all five steps PASSED. On VERIFIED -> work becomes DELIVERED. On MISMATCH -> persisted in verifications/audit/errors/checkpoints and returns structured error (never silently promoted).",
        inputSchema={
            "type": "object",
            "properties": {
                "work_id": {"type": "string"},
                "expected": {"type": "string"},
                "actual": {"type": "string"},
                "note": {"type": "string", "description": "Optional note"},
            },
            "required": ["work_id", "expected", "actual"],
        },
    ),
    Tool(
        name="get_work_status",
        description="Return full evidence for a work unit: work metadata, step_runs, errors, checkpoints, audit_log, verifications.",
        inputSchema={
            "type": "object",
            "properties": {"work_id": {"type": "string"}},
            "required": ["work_id"],
        },
    ),
    Tool(
        name="add_evidence",
        description="Record a verified evidence item (id, status, topic, fact, source, verification_state). Duplicate id returns CONFLICT.",
        inputSchema={
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "status": {"type": "string"},
                "topic": {"type": "string"},
                "fact": {"type": "string"},
                "source": {"type": "string"},
                "verification_state": {"type": "string"},
            },
            "required": ["id", "status", "topic", "fact", "source", "verification_state"],
        },
    ),
    Tool(
        name="list_evidence",
        description="List all recorded evidence items.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="health",
        description="Health check: confirms DB is reachable and returns IRIS version + db path.",
        inputSchema={"type": "object", "properties": {}},
    ),
]


@server.list_tools()
async def list_tools() -> list[Tool]:
    return _TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "health":
            try:
                database.init_db()
                with database.get_connection() as conn:
                    conn.execute("SELECT 1").fetchone()
                return _ok({"status": "ok", "database": "ok", "db_path": str(database.get_db_path())})
            except Exception as exc:
                return _err("DB_UNAVAILABLE", f"database unavailable: {exc}")

        if name == "create_work":
            work_id = str(arguments.get("work_id", "")).strip()
            title = str(arguments.get("title", "")).strip()
            if not work_id or not title:
                return _err("VALIDATION", "work_id and title are required and non-empty")
            try:
                create_work(work_id, title)
            except Exception as exc:
                if "UNIQUE" in str(exc) or "UNIQUE constraint" in str(exc):
                    return _err("CONFLICT", f"work id '{work_id}' already exists")
                return _err("INTERNAL", f"create_work failed: {exc}")
            return _ok({"work_id": work_id, "title": title, "work_status": "CREATED"})

        if name == "run_step":
            work_id = str(arguments.get("work_id", "")).strip()
            step = arguments.get("step")
            expected = str(arguments.get("expected", "")).strip()
            actual = str(arguments.get("actual", "")).strip()
            note = str(arguments.get("note", ""))[:2000]
            fail_attempts = int(arguments.get("fail_attempts", 0))
            max_attempts = int(arguments.get("max_attempts", 10))
            if not work_id or step is None or not expected or not actual:
                return _err("VALIDATION", "work_id, step, expected, actual are required")
            try:
                step = int(step)
            except (TypeError, ValueError):
                return _err("VALIDATION", "step must be an integer 1-5")
            try:
                result = run_step(work_id, step, expected, actual, note, fail_attempts, max_attempts)
                return _ok(result)
            except ValueError as exc:
                return _err("GATE_VIOLATION", str(exc))
            except RuntimeError as exc:
                return _err("ATTEMPTS_EXHAUSTED", str(exc))
            except Exception as exc:
                return _err("INTERNAL", f"run_step failed: {exc}")

        if name == "final_verify":
            work_id = str(arguments.get("work_id", "")).strip()
            expected = str(arguments.get("expected", "")).strip()
            actual = str(arguments.get("actual", "")).strip()
            note = str(arguments.get("note", ""))[:2000]
            if not work_id or not expected or not actual:
                return _err("VALIDATION", "work_id, expected, actual are required")
            result = _final_verify_persist(work_id, expected, actual, note)
            if result.get("status") == "OK":
                return _ok(result)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        if name == "get_work_status":
            work_id = str(arguments.get("work_id", "")).strip()
            if not work_id:
                return _err("VALIDATION", "work_id is required")
            result = get_work(work_id)
            if not result:
                return _err("NOT_FOUND", f"work {work_id} not found")
            return _ok(result)

        if name == "add_evidence":
            required = ["id", "status", "topic", "fact", "source", "verification_state"]
            missing = [k for k in required if not str(arguments.get(k, "")).strip()]
            if missing:
                return _err("VALIDATION", f"missing required fields: {missing}")
            vals = tuple(str(arguments[k]).strip() for k in required)
            try:
                with database.get_connection() as conn:
                    conn.execute(
                        "INSERT INTO evidence(id,status,topic,fact,source,verification_state) VALUES(?,?,?,?,?,?)",
                        vals,
                    )
            except Exception as exc:
                if "UNIQUE" in str(exc):
                    return _err("CONFLICT", f"evidence id '{arguments['id']}' already exists")
                return _err("INTERNAL", f"add_evidence failed: {exc}")
            return _ok({"evidence_id": arguments["id"], "recorded": True})

        if name == "list_evidence":
            items = database.many("SELECT * FROM evidence ORDER BY created_at, id")
            return _ok({"items": items, "count": len(items)})

        return _err("UNKNOWN_TOOL", f"tool '{name}' is not implemented")
    except Exception as exc:
        return _err("INTERNAL", f"unhandled error in {name}: {exc}")


async def main() -> None:
    database.init_db()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
