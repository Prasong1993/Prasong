# IRIS Five-Step Execution Contract
Status: IMPLEMENTED + TESTED (v0.6.5, 23/23 tests PASS)

For each step: CHECK → DO → VERIFY. If verification fails, record the error and
checkpoint, correct/retry, and verify again. Advance only after PASS. Preserve
all failures (never erase).

1. แนวคิด
2. ออกแบบ
3. ทำงานจริง
4. ส่งผล
5. ตรวจสอบบนพื้นที่ ChatGPT

Final delivery requires all five steps to PASS plus final expected-vs-actual
verification to be VERIFIED → work status becomes DELIVERED.

## Execution boundaries (proven in v0.6.5)
- REST API path: `runtime/main.py` (FastAPI) — mismatch persisted in `verifications` + `audit_log`.
- MCP path: `runtime/mcp_server.py` (stdio) — mismatch persisted identically (parity with REST).
- Both paths share the same `controller.py` + `database.py` (SQLite).
- Database path is overridable via `IRIS_DB_PATH` env var (test isolation proven).
- MCP tools return structured `{"status":"OK"|"ERROR", "error_type":..., "message":...}` — never raw exceptions.

## What is UNPROVEN until you test it on the target host
- That the Plugin Creator host actually binds `.mcp.json` and launches `python runtime/mcp_server.py`.
- That the host's Python environment has `mcp>=1.0` installed.
- Production-scale concurrency / multi-user isolation.
