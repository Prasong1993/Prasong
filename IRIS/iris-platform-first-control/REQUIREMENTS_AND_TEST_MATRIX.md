# Requirements and Test Matrix
Project: IRIS Platform-First Control
Status: Core implementation exists; trusted source verification, MCP host, and mobile integration remain unverified.
Date: 2026-10-11
Working branch: work/iris-control-renovation-20261011-copy

## Scope and boundaries
- ChatGPT/OpenAI is the preferred user and model platform, subject to actual account/client support.
- IRIS is a thin deterministic control plane for project/task state, permissions, checkpoints, evidence, idempotency, and audit.
- Do not modify main or merge this branch as part of this project.
- No API key, OAuth token, or secret may be committed or copied into logs.

## Requirements and acceptance tests

| ID | Requirement | Acceptance test | Evidence required | Current status |
|---|---|---|---|---|
| R-01 | Every task has stable project/task/correlation identifiers. | Create tasks and verify unique IDs persist on read-back. | Local unit test and GitHub source read-back. | PARTIAL: project/task IDs pass; explicit Trace ID not implemented. |
| R-02 | State transitions are deterministic and gated. | Attempt valid and invalid transitions; invalid transitions must fail without advancing state. | Test output plus persisted rejection event. | PARTIAL: main gate transitions tested; full transition matrix NOT RUN. |
| R-03 | Evidence is provenance-aware and cannot self-assert VERIFIED. | Submit incomplete evidence; try client-supplied VERIFIED; test matching and mismatching trusted verification receipts. | Evidence digest, verifier receipt, and audit events. | PARTIAL: client self-assertion is rejected; digest mismatch is audited; real source-fetch verifier NOT IMPLEMENTED. |
| R-04 | Execute is blocked until policy gates pass. | Attempt execution before verified evidence/approval; verify no side effect is invoked. | Unit test and safe adapter. | PASS for core gate simulation; MCP ingress stays UNKNOWN until a trusted verifier is implemented. |
| R-05 | Tool routing does not imply invocation or permission. | Ensure authorization does not claim invocation. | Adapter registry and test output. | PARTIAL: invocation_performed=false; actual adapter registry/routing not implemented. |
| R-06 | Side effects are idempotent where possible. | Replay an idempotency key and reject changed arguments. | Persistent idempotency record and test. | PASS for authorization idempotency; external side-effect idempotency NOT RUN. |
| R-07 | State survives restart and can recover from a checkpoint. | Reopen DB, restore checkpoint, reset approval, and do not replay side effects. | State and audit output. | PASS in local SQLite unit tests; deployed storage/restart NOT RUN. |
| R-08 | Audit history is append-only and secrets are redacted. | Inspect success/failure audit events and secret-shaped values. | Audit assertions and redaction test. | PARTIAL: append events and common-string redaction tested; tamper resistance/broader corpus NOT RUN. |
| R-09 | Errors are captured and safely retried. | Inject denied permission, digest mismatch, unknown outcome, timeout, and storage failure. | Failure-path tests and ledger. | PARTIAL: permission denial, digest mismatch, and UNKNOWN_OUTCOME tested; timeout/storage failure NOT RUN. |
| R-10 | Budget, rate limit, timeout, and retry policy are explicit. | Simulate limit exhaustion and timeout; verify bounded handling. | Configuration and tests. | NOT RUN. |
| R-11 | OpenAI integration follows current schemas and permissions. | Validate request/tool schema and an authorized API test. | Request/response fixtures and account evidence. | PARTIAL: official docs reviewed; no API request or account permission test. |
| R-12 | ChatGPT app/connector setup is supported. | Connect a test app/server and exercise a read-only tool first. | Host logs and connection evidence. | NOT RUN. |
| R-13 | ChatGPT Mobile behavior is verified separately. | Test discovery, connection, read, write approval, and failures on the actual mobile client/account. | Dated client/version record. | NOT RUN; mobile-only capability UNKNOWN. |
| R-14 | Branch changes are isolated and reviewable. | Compare working branch with source branch and main separately. | GitHub compare and file list. | PASS relative to source branch: only project-local paths listed; main comparison includes older/inherited IRIS changes. |
| R-15 | Delivery claims match evidence. | Map every requirement to PASS/PARTIAL/UNKNOWN/BLOCKED/NOT RUN. | Final acceptance report. | NOT RUN; final acceptance review remains open. |

## Local test evidence
- Command: `python -m py_compile runtime/control_plane.py runtime/verified_control_plane.py runtime/mcp_server.py` and `python -m unittest discover -v`.
- Latest development-worktree result: **12 tests passed, 0 failed** after adding the trusted evidence boundary.
- Coverage: unique IDs/health, UNKNOWN evidence gate, client self-assertion rejection, verifier digest mismatch audit, execution authorization without invocation, permission denial/audit, idempotency/reuse mismatch, restart persistence, checkpoint recovery with approval reset, final verification reference, UNKNOWN_OUTCOME blocking, and secret-shaped redaction.
- Limitation: the MCP SDK is not installed in the local environment. MCP adapter import, protocol/transport behavior, ChatGPT host integration, and mobile behavior are NOT RUN. The unit tests exercise the core and trusted-verifier boundary; branch source files are separately read back.

## Verification levels
1. Static: schemas, state machine, permissions, dependencies.
2. Unit: deterministic policy/state/idempotency/redaction/trusted-verifier boundary.
3. Integration: database restart/recovery, MCP adapter, and actual adapter tests.
4. Failure-path: timeout, malformed payload, duplicate request, denied permission, digest mismatch, and persistence failure.
5. Host: actual ChatGPT connection and tool invocation in the target account.
6. Mobile: actual iOS/Android behavior; do not infer from API tests.
7. Release review: branch diffs, secret leakage, unsupported capabilities.

## Stop conditions
- Stop and report BLOCKED if target branch, permission, or test environment cannot be established.
- Do not bypass authentication, approval, rate limits, or host security controls to obtain a PASS.
- On write/ingestion warnings, inspect the exact response and reduce only structurally safe payloads; read back after each successful write.
- Never mark a requirement PASS based only on search results, source inspection, or an unexecuted plan.
- Aggregate ordinary errors for milestone 10 review; raise urgent security/privacy risks immediately.

## Architecture gate
- ARCHITECTURE_DECISION.md records a provisional ChatGPT Apps SDK + MCP path, conditional on account/mobile support; Responses API with custom UI is a fallback.
- The remote write-capable server remains BLOCKED until authentication, TLS, least privilege, approval policy, trusted evidence verification, and secrets management are configured and tested.
- Mobile/account support remains UNKNOWN until tested in the intended account/client.
