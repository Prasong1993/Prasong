"""MCP-layer tests — call the MCP server's call_tool directly (no stdio).

Covers: health, create_work (incl. duplicate CONFLICT), run_step gate,
run_step recovery, real mismatch exhaustion, final_verify gate,
final_verify mismatch PERSISTED (the v0.6.x bug), final_verify VERIFIED,
get_work_status full evidence, add_evidence + duplicate, list_evidence.
Every tool must return {"status": "OK"|"ERROR", ...} — never raise.
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runtime"))

# Isolate DB BEFORE importing mcp_server (which imports database)
os.environ["IRIS_DB_PATH"] = str(Path(tempfile.mkdtemp()) / "iris_mcp_test.db")

import database  # noqa: E402
database.init_db()

from mcp_server import call_tool  # noqa: E402


def call(name, **args):
    """Synchronous wrapper around the async MCP call_tool. Returns parsed dict."""
    import json
    result = asyncio.run(call_tool(name, args))
    text = result[0].text
    return json.loads(text)


def test_health_ok():
    r = call("health")
    assert r["status"] == "OK"
    assert r["database"] == "ok"
    assert "iris_mcp_test.db" in r["db_path"]


def test_create_work_ok():
    r = call("create_work", work_id="MCP-W1", title="mcp create")
    assert r["status"] == "OK"
    assert r["work_status"] == "CREATED"


def test_create_work_duplicate_returns_structured_conflict():
    call("create_work", work_id="MCP-DUP", title="first")
    r = call("create_work", work_id="MCP-DUP", title="second")
    assert r["status"] == "ERROR"
    assert r["error_type"] == "CONFLICT"  # NOT a raw Python exception


def test_cannot_skip_step():
    call("create_work", work_id="MCP-SKIP", title="skip gate")
    r = call("run_step", work_id="MCP-SKIP", step=3, expected="x", actual="x")
    assert r["status"] == "ERROR"
    assert r["error_type"] == "GATE_VIOLATION"


def test_step1_recovery_then_all_pass_then_final_verified():
    call("create_work", work_id="MCP-FULL", title="full mcp flow")
    # step 1: simulate 1 failure then recover (expected==actual)
    r = call("run_step", work_id="MCP-FULL", step=1, expected="s1", actual="s1", fail_attempts=1)
    assert r["status"] == "OK" and r["attempt"] == 2
    for i in [2, 3, 4, 5]:
        r = call("run_step", work_id="MCP-FULL", step=i, expected=f"s{i}", actual=f"s{i}")
        assert r["status"] == "OK", f"step {i} failed: {r}"
    r = call("final_verify", work_id="MCP-FULL", expected="final", actual="final")
    assert r["status"] == "OK"
    assert r["verification_status"] == "VERIFIED"
    assert r["delivered"] is True


def test_final_verify_before_5_steps_returns_gate_error():
    call("create_work", work_id="MCP-EARLY", title="early")
    call("run_step", work_id="MCP-EARLY", step=1, expected="a", actual="a")
    r = call("final_verify", work_id="MCP-EARLY", expected="x", actual="x")
    assert r["status"] == "ERROR"
    assert r["error_type"] == "GATE_VIOLATION"


def test_final_verify_mismatch_is_persisted_and_not_delivered():
    """The critical v0.6.x bug: MCP mismatch was returned but NOT persisted.
    Now it MUST land in verifications + audit_log + errors + checkpoints."""
    call("create_work", work_id="MCP-MISMATCH", title="final mismatch")
    for i in [1, 2, 3, 4, 5]:
        call("run_step", work_id="MCP-MISMATCH", step=i, expected=f"e{i}", actual=f"e{i}")
    r = call("final_verify", work_id="MCP-MISMATCH", expected="A", actual="B")
    assert r["status"] == "ERROR"
    assert r["error_type"] == "FINAL_MISMATCH"
    assert r["persisted"] is True
    assert r["verification_status"] == "MISMATCH"
    # Confirm persistence via get_work_status
    st = call("get_work_status", work_id="MCP-MISMATCH")
    assert st["status"] == "OK"
    verifs = st["verifications"]
    assert len(verifs) >= 1
    assert verifs[-1]["status"] == "MISMATCH"
    assert len(st["errors"]) >= 1  # error retained
    assert len(st["checkpoints"]) >= 1  # checkpoint retained
    assert st["work"]["status"] != "DELIVERED"  # must NOT be delivered


def test_real_mismatch_exhausts_attempts():
    call("create_work", work_id="MCP-EXH", title="exhaust")
    r = call("run_step", work_id="MCP-EXH", step=1, expected="X", actual="Y", max_attempts=2)
    assert r["status"] == "ERROR"
    assert r["error_type"] == "ATTEMPTS_EXHAUSTED"


def test_get_work_status_returns_full_evidence():
    st = call("get_work_status", work_id="MCP-FULL")
    assert st["status"] == "OK"
    assert len(st["steps"]) > 0
    assert len(st["errors"]) > 0  # recovery failure retained
    assert len(st["checkpoints"]) > 0
    assert len(st["audit"]) > 0
    assert len(st["verifications"]) > 0
    assert st["work"]["status"] == "DELIVERED"


def test_add_evidence_and_duplicate_conflict():
    r = call("add_evidence", id="EV-MCP-1", status="VERIFIED", topic="t",
             fact="f", source="s", verification_state="VERIFIED")
    assert r["status"] == "OK"
    r = call("add_evidence", id="EV-MCP-1", status="VERIFIED", topic="t",
             fact="f", source="s", verification_state="VERIFIED")
    assert r["status"] == "ERROR"
    assert r["error_type"] == "CONFLICT"


def test_list_evidence():
    r = call("list_evidence")
    assert r["status"] == "OK"
    assert r["count"] >= 1


def test_unknown_tool_returns_structured_error():
    r = call("nonexistent_tool")
    assert r["status"] == "ERROR"
    assert r["error_type"] == "UNKNOWN_TOOL"


def test_invalid_step_6_rejected():
    r = call("run_step", work_id="MCP-FULL", step=6, expected="x", actual="x")
    assert r["status"] == "ERROR"
