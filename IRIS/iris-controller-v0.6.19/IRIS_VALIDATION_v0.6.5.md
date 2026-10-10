# IRIS Controller v0.6.5 — Validation Record (REAL EVIDENCE)

## Final Status
READY_FOR_PLUGIN_INSTALLATION (host-side MCP binding still requires target-host proof)

## Test evidence (executed in VM, 2026-10-08)
- Unit/integration tests: **23/23 PASS** (`python -m pytest tests/ -v`)
  - test_controller.py: 3 (core controller, gates, recovery)
  - test_api.py: 7 (REST API layer, 409/422/404, evidence)
  - test_mcp.py: 13 (MCP tools, structured errors, mismatch persistence)
- MCP stdio E2E (real subprocess + JSON-RPC): **19/19 PASS**
  - initialize handshake, tools/list (7 tools), create_work, run_step 1-5 (with recovery),
    final_verify VERIFIED → DELIVERED, get_work_status (errors=1, checkpoints=6, audit=31, verifications=1),
    final_verify MISMATCH persisted into verifications+audit+errors+checkpoints.

## Validation Matrix
| Area | Result | Evidence |
|---|---|---|
| Core Controller | PASS | test_controller.py 3/3 |
| Gate Enforcement (no skip) | PASS | REST 409 + MCP GATE_VIOLATION |
| Workflow Execution (5 steps) | PASS | stdio E2E step 1-5 all PASS |
| Final Verification | PASS | VERIFIED → DELIVERED; MISMATCH → retained, not delivered |
| MCP Workflow (stdio) | PASS | 19/19 stdio E2E |
| Failure / Recovery | PASS | fail_attempts=1 → attempt=2 PASS; errors retained |
| Persistence / Database | PASS | SQLite 7 tables; IRIS_DB_PATH env override works |
| End-to-End Delivery | PASS | CREATED → 5×PASS → VERIFIED → DELIVERED |
| MCP Structured Errors | PASS | CONFLICT / GATE_VIOLATION / ATTEMPTS_EXHAUSTED / FINAL_MISMATCH / UNKNOWN_TOOL — never raw exceptions |
| MCP Mismatch Persistence (critical fix) | PASS | MISMATCH row in verifications + audit + errors + checkpoints (was broken in v0.6.x) |
| Plugin Manifest | PASS | .codex-plugin/plugin.json + plugin.json aligned v0.6.5; defaultPrompt is list[str]; mcpServers=./.mcp.json |
| Dependencies | PASS | requirements.txt valid pip format (was broken Markdown table) |

## Fixes applied (v0.6.2 → v0.6.5)
1. `requirements.txt`: broken Markdown table → valid pip format + added `mcp>=1.0,<2`.
2. `database.py`: now reads `IRIS_DB_PATH` env var (test isolation proven).
3. Added `runtime/mcp_server.py`: real MCP stdio server, 7 tools.
4. MCP `final_verify`: mismatch now persisted (parity with REST) — was NOT persisted in v0.6.x.
5. MCP `run_step`: accepts real `expected` + `actual` (not derived from a status flag).
6. MCP errors: structured `{status:ERROR, error_type, message}` — never raw exceptions.
7. Manifests: `defaultPrompt` → list[str] per OpenAI spec; added `mcpServers`; version aligned to 0.6.5.
8. Added `.mcp.json`, `tests/test_mcp.py`, `tests/test_api.py`; renamed docs to FIVE_STEP.

## Still UNPROVEN (must verify on the actual Plugin Creator host)
- That the host binds `.mcp.json` and launches `python runtime/mcp_server.py` successfully.
- That the host's Python has `mcp>=1.0` (install with `pip install -r runtime/requirements.txt`).
- Multi-user / concurrency behavior.
