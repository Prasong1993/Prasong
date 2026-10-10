# IRIS Control Renovation — Evidence and Status

Date: 2026-10-11
Working branch: `work/iris-control-renovation-20261011`
Scope: `IRIS/iris-controller-v0.6.5/` only

## Source evidence

- Repository: https://github.com/Prasong1993/Prasong
- Target README: https://github.com/Prasong1993/Prasong/blob/main/IRIS/iris-controller-v0.6.5/README.md
- Existing database layer: https://github.com/Prasong1993/Prasong/blob/main/IRIS/iris-controller-v0.6.5/runtime/database.py
- Existing MCP server: https://github.com/Prasong1993/Prasong/blob/main/IRIS/iris-controller-v0.6.5/runtime/mcp_server.py
- MCP tool-list/call contract (official): https://modelcontextprotocol.io/specification/2025-06-18/server/tools
- MCP introduction (official): https://modelcontextprotocol.io/docs/2026-07-28/getting-started/intro

Repository source was read directly during this work. Previous validation documents were treated as RECOVERED historical claims, not as current test results.

## Changes on this branch

1. `runtime/database.py`
   - Preserves the original seven tables and adds idempotent, additive schema creation.
   - Adds schema version tracking and tables for projects, tasks, dependencies, requirements, source evidence, decisions, evidence links, tool registry, tool calls, policies, policy decisions, work events, recovery points, verification results, runtime state, and record revisions.
   - Adds `record_event` and `runtime_status` readback helpers.
   - Enables SQLite foreign-key checks and a bounded busy timeout per connection.

2. `runtime/controller.py`
   - Emits persisted work/step/error/checkpoint events and exposes event/tool-call history through work status.
   - Existing legacy work tables remain in place.

3. `runtime/main.py`
   - Adds `GET /runtime/status` for reading persisted runtime state.
   - Retains REST final-verification mismatches in errors and checkpoints as well as verification/audit records.
   - Reports the resolved database path from health checks.

4. Tests
   - Adds a migration idempotency and event readback test.
   - Extends REST tests for mismatch retention and runtime status retrieval.

## Status boundaries

- SOURCE VERIFIED: target files and the official MCP tool contract were inspected.
- IMPLEMENTATION VERIFIED: branch files and commit responses confirm the changes were written to GitHub.
- TESTS VERIFIED: NOT YET. A fresh test run has not been executed in this environment; GitHub combined status returned no checks for the inspected commit at the time of review.
- DATABASE VERIFIED: NOT YET. The added test is present, but no live database test run/readback has been executed here.
- RUNTIME VERIFIED: NOT YET. No running server instance was available for runtime event inspection.
- CHATGPT HOST VERIFIED: NOT VERIFIED. The target host has not been exercised.

## Remaining implementation work

The schema provides storage primitives, but this branch does not yet implement a complete deterministic Policy Gate, dependency-aware Orchestrator, Tool Call lifecycle persistence around every MCP invocation, idempotency enforcement at dispatch, or automatic recovery/resume. These must not be represented as implemented merely because corresponding tables exist. Parallel execution capability remains UNKNOWN until the actual host is tested.

No commit was pushed to `main`, no historical database was migrated in place, and no ChatGPT Host test was claimed.
