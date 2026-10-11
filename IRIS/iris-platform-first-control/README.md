# IRIS Platform-First Control

A new, isolated control-plane implementation. ChatGPT/OpenAI remains the preferred interaction and model platform; this repository adds deterministic policy gates, durable task/evidence metadata, checkpoints, idempotency, and audit only where needed.

## Current verification status

- Deterministic SQLite core: implemented and locally unit-tested in the development workspace.
- Trusted source verifier: implemented in `runtime/source_verifier.py`. It fetches only allowlisted HTTPS hosts, rejects query parameters and redirects, checks public DNS results for live fetches, enforces a timeout and body-size limit, and records only the content digest/provenance. **VERIFIED means source retrieval and digest integrity only; it does not prove the semantic truth of the claim.**
- MCP adapter: the official MCP Python SDK 2.3.0 was installed in GitHub Actions; compile and a real stdio protocol test passed on baseline commit `21f73554d9c7c2034a145d1d6d4dc55c7a8fb8a8`. Authenticated remote transport and ChatGPT host behavior remain **NOT RUN**.
- ChatGPT Apps SDK/account/mobile connection: **NOT RUN**.
- Public deployment: **BLOCKED** until authenticated transport, least-privilege permissions, and hosting are configured and tested.

## Local tests

From the project root:

```bash
python -m unittest discover -v
```

## MCP development

The official PyPI package page reported MCP Python SDK 2.3.0, released 2026-10-02, during project research. Install the declared dependency and use the official SDK CLI:

```bash
uv run --with "mcp[cli]>=2.3.0,<3.0.0" mcp dev runtime/mcp_server.py
```

This is a development/inspection path, not proof of ChatGPT connectivity. Do not expose write-capable MCP tools publicly until transport authentication, TLS, least-privilege permissions, approval policy, and secret management are configured and tested.

## AI action journal and resuming work

Every tool call routed through the IRIS MCP adapter is intended to create an append-only `STARTED` event before the operation and a terminal event afterward. Records include action/session/trace IDs, tool name, task link when available, redacted input/output metadata, and result/error status. If the process stops before a terminal event, the `STARTED` event remains as an unresolved action; inspect it before retrying. Use `get_agent_actions` to inspect the action history and `get_resume_context` to retrieve task state, latest checkpoint metadata, audit events, and recorded actions.

The process session ID is not a verified ChatGPT conversation ID, and the caller identity is explicitly unverified until authenticated transport is implemented. This journal covers observable IRIS MCP tool calls only; it does not record hidden model reasoning or activity outside this adapter. Do not treat a missing record as proof that an external action did not occur.

## Safety contract

- The core does not call a model and does not invoke external tools.
- The MCP evidence tool fetches the source server-side; clients cannot submit raw content or self-assert `VERIFIED`.
- `authorize_execution` returns `invocation_performed: false`; an actual authorized host adapter must execute the action and report its real result.
- Only `VERIFIED` source-retrieval evidence satisfies the initial gate. `RECOVERED`, `UNKNOWN`, `BLOCKED`, and `NOT RUN` remain distinct.
- Unknown external outcomes block the task rather than triggering an unsafe blind retry.
- Checkpoint recovery restores planning state, resets approval, and never replays an in-flight side effect.
- Audit payloads redact common secret-shaped values; callers must still avoid sending secrets in inputs.
