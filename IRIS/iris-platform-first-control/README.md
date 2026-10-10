# IRIS Platform-First Control

A new, isolated control-plane implementation. ChatGPT/OpenAI remains the preferred interaction and model platform; this repository adds deterministic policy gates, durable task/evidence metadata, checkpoints, idempotency, and audit only where needed.

## Current verification status

- Deterministic SQLite core: implemented and locally unit-tested in the development workspace.
- MCP adapter: authored against the current official MCP Python SDK interface; the SDK is not installed in the local test environment, so adapter import and host behavior are **NOT RUN**.
- ChatGPT Apps SDK/account/mobile connection: **NOT RUN**.
- Public deployment: **BLOCKED** until authenticated transport, least-privilege permissions, and hosting are configured and tested.

## Local tests

From the project root:

```bash
python -m unittest discover -v
```

## MCP development

Install the dependency in `runtime/requirements.txt`, then use the current official MCP SDK CLI:

```bash
uv run --with "mcp[cli]>=2.0.0,<3.0.0" mcp dev runtime/mcp_server.py
```

This is a development/inspection path, not proof of ChatGPT connectivity. Do not expose write-capable MCP tools publicly until transport authentication, TLS, least-privilege permissions, approval policy, and secret management are configured and tested.

## Safety contract

- The core does not call a model and does not invoke external tools.
- `authorize_execution` returns `invocation_performed: false`; an actual authorized host adapter must execute the action and report its real result.
- Only `VERIFIED` evidence satisfies the initial execution gate. `RECOVERED`, `UNKNOWN`, `BLOCKED`, and `NOT RUN` remain distinct and do not silently become proof.
- Unknown external outcomes block the task rather than triggering an unsafe blind retry.
- Checkpoint recovery restores planning state, resets approval, and never replays an in-flight side effect.
- Audit payloads redact common secret-shaped values; callers must still avoid sending secrets in inputs.
