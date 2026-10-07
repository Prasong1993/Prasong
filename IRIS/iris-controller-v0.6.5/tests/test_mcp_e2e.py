import asyncio
import json
import os
import tempfile
from pathlib import Path

os.environ["IRIS_DB_PATH"] = str(Path(tempfile.mkdtemp()) / "iris_mcp_e2e.db")
from runtime.mcp_server import call_tool

def call(name, **args):
    result = asyncio.run(call_tool(name, args))
    return json.loads(result[0].text)

def test_mcp_full_e2e():
    wid="mcp-e2e-065"
    assert call("create_work", work_id=wid, title="MCP E2E")["status"] == "OK"
    for step in range(1, 6):
        r=call("run_step", work_id=wid, step=step, expected=f"E{step}", actual=f"E{step}")
        assert r["status"] == "OK"
    r=call("final_verify", work_id=wid, expected="MATCH", actual="MATCH")
    assert r["status"] == "OK"
    assert r["verification_status"] == "VERIFIED"
    st=call("get_work_status", work_id=wid)
    assert st["status"] == "OK"
    assert st["work"]["status"] == "DELIVERED"
