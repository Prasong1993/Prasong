# IRIS Platform-First Control

A new, isolated control-plane implementation. ChatGPT/OpenAI remains the preferred interaction and model platform; this repository adds deterministic policy gates, durable task/evidence metadata, checkpoints, idempotency, and audit only where needed.

## Current verification status

- Deterministic SQLite core: implemented and locally unit-tested in the development workspace.
- Trusted evidence boundary: implemented in `runtime/verified_control_plane.py`. The MCP-facing evidence tool always records `UNKNOWN`; only trusted server-side verification code may call `mark_evidence_verified`. A production source-fetch/verification adapter is **NOT IMPLEMENTED**, so real incoming evidence cannot yet unlock the execution gates.
- MCP adapter: authored against the current official MCP Python SDK interface. The development environment did not have the SDK installed, so adapter import and host behavior are **NOT RUN**.
- ChatGPT Apps SDK/account/mobile connection: **NOT RUN**.
- Public deployment: **BLOCKED** until authenticated transport, least-privilege permissions, a trusted source verifier, and hosting are configured and tested.

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

## Safety contract

- The core does not call a model and does not invoke external tools.
- The MCP client cannot self-assert `VERIFIED`; incoming evidence is stored as `UNKNOWN` until a trusted server-side verifier validates the source and digest.
- `authorize_execution` returns `invocation_performed: false`; an actual authorized host adapter must execute the action and report its real result.
- Only `VERIFIED` evidence satisfies the initial execution gate. `RECOVERED`, `UNKNOWN`, `BLOCKED`, and `NOT RUN` remain distinct and do not silently become proof.
- Unknown external outcomes block the task rather than triggering an unsafe blind retry.
- Checkpoint recovery restores planning state, resets approval, and never replays an in-flight side effect.
- Audit payloads redact common secret-shaped values; callers must still avoid sending secrets in inputs.
