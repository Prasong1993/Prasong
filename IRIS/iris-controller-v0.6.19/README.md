# IRIS Controller v0.6.18 — Runtime Persistence and Execution Contract

IRIS provides a five-step gated work record, SQLite evidence storage, deterministic step transitions, checkpoints, audit history, and a capability registry.

## Runtime telemetry
- MCP tool calls are recorded in SQLite with a generated Tool Call ID and Trace ID, start/result timestamps, result status, and error details.
- `runtime_status` reads back the latest persisted event, active tool calls, checkpoint, error, and verification.
- REST exposes the same database through `/health`, `/runtime/status`, `/work`, `/work/{id}`, `/evidence`, and verification endpoints.
- Schema changes are additive and versioned; `schema_migrations` records the current control-plane schema version.

## Actual tool execution boundary
- `register_tool` only records a declaration for a tool explicitly exposed by a real adapter.
- `route_tool` deterministically selects an eligible registered capability. It does **not** invoke the selected provider.
- The MCP server does not automatically discover all tools exposed by ChatGPT. The IRIS skill directs the model to call actual host tools when they are available and authorized.
- Parallel execution is used only if the actual host supports it and dependency/side-effect rules allow it.

## Proof levels
Source inspection, local tests, database read-back, live MCP/REST runtime, and ChatGPT-host verification are separate. A successful local test is not evidence that the ChatGPT host loaded or executed this release.


## v0.6.19 renovation
- Align REST runtime version with package version 0.6.19.
- Route MCP startup through `runtime/launch_mcp.py` so tool responses report 0.6.19.
- See `docs/RENOVATION_v0.6.19.md` for evidence and verification limits.
