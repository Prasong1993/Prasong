# IRIS Controller v0.6.5

Evidence-first five-step execution controller, packaged as a Codex/MCP plugin.

## Five steps (gated, in order)
1. แนวคิด
2. ออกแบบ
3. ทำงานจริง
4. ส่งผล
5. ตรวจสอบบนพื้นที่ ChatGPT

Each step uses CHECK → DO → VERIFY. Failure is retained with error/checkpoint/audit
records, corrected/retried, and verified again. Delivery requires all five steps
PASS plus final expected-vs-actual verification VERIFIED → status DELIVERED.

## Runtime
Python / FastAPI (REST) + MCP stdio server / SQLite. The controller preserves
evidence, errors, checkpoints, audit records and verifications.

Database path: `IRIS_DB_PATH` environment variable (fallback: `runtime/data/iris.db`).

## Install dependencies
```bash
pip install -r runtime/requirements.txt
```

## Run as MCP server (for Codex Plugin Creator / Claude Desktop)
The plugin ships `.mcp.json` which launches:
```bash
python runtime/mcp_server.py
```
Tools exposed: `health`, `create_work`, `run_step`, `final_verify`,
`get_work_status`, `add_evidence`, `list_evidence`.

## Run REST API (optional, for direct HTTP use)
```bash
uvicorn runtime.main:app --reload --port 8000
```
Endpoints: `GET /`, `GET /health`, `GET /structure`, `POST /work`,
`GET /work/{id}`, `POST /work/{id}/step/{1..5}`, `POST /work/{id}/verify`,
`GET /evidence`, `POST /evidence`.

## Test
```bash
python -m pytest tests/ -v
```

## Package structure (Codex plugin)
```
iris-controller/
├── .codex-plugin/plugin.json   # required manifest (OpenAI Codex)
├── plugin.json                 # agent-plugins.org manifest (cross-host)
├── .mcp.json                   # MCP server launch config
├── skills/iris/SKILL.md        # agent instructions
├── runtime/
│   ├── mcp_server.py           # MCP stdio server (entry point)
│   ├── main.py                 # FastAPI REST (optional)
│   ├── controller.py           # 5-step gated workflow engine
│   ├── database.py             # SQLite (IRIS_DB_PATH aware)
│   ├── model.py                # step definitions + status enum
│   ├── verify.py               # expected-vs-actual helper
│   └── requirements.txt
├── tests/                      # unit + MCP + API tests
└── docs/
```

## v0.6.5 changelog (fixed from v0.6.2)
- Fixed: `requirements.txt` was a broken Markdown table → now valid pip format.
- Fixed: `database.py` now reads `IRIS_DB_PATH` env var (test isolation works).
- Added: `runtime/mcp_server.py` — real MCP stdio server with 7 tools.
- Fixed: MCP `final_verify` now persists MISMATCH into verifications/audit/errors/checkpoints (parity with REST).
- Fixed: MCP `run_step` accepts real `expected` + `actual` (not derived from a status flag).
- Fixed: MCP tools return structured errors (`status:ERROR` + `error_type` + `message`), never raw exceptions.
- Fixed: `defaultPrompt` is now a list[str] per OpenAI spec (was a bare string).
- Added: `.mcp.json` + `mcpServers` field in both manifests.
- Added: `tests/test_mcp.py` and `tests/test_api.py` (E2E coverage).
- Version aligned across all manifests, README and runtime to 0.6.5.
