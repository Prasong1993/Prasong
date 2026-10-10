# Requirements and Test Matrix
Project: IRIS Platform-First Control
Status: Core implementation exists; host/mobile and MCP SDK integration remain unverified.
Date: 2026-10-11
Working branch: work/iris-control-renovation-20261011-copy

## Scope and boundaries
- ChatGPT/OpenAI is the preferred user and model platform, subject to actual account/client support.
- IRIS is a thin deterministic control plane for project/task state, permissions, checkpoints, evidence, idempotency, and audit.
- Reuse supported OpenAI capabilities where they fit. Do not recreate the model loop, tool orchestration, or tracing without a demonstrated gap.
- Do not modify main or merge this branch as part of this project.
- No API key, OAuth token, or secret may be committed or copied into logs.

## Requirements and acceptance tests

| ID | Requirement | Acceptance test | Evidence required | Current status |
|---|---|---|---|---|
| R-01 | Every task has stable project/task/correlation identifiers. | Create tasks and verify unique IDs persist on read-back. | Local unit test for task identity; GitHub source read-back. | PASS for project/task IDs in local core tests; Trace ID not yet implemented. |
| R-02 | State transitions are deterministic and gated. | Attempt valid and invalid transitions; invalid transitions must fail without advancing state. | Test output plus persisted rejection event. | PARTIAL: key gate transitions tested; full invalid-transition matrix NOT RUN. |
| R-03 | Evidence is provenance-aware. | Submit evidence with missing source, timestamp, digest, or invalid status; reject incomplete evidence. | Validation tests and evidence rows. | PARTIAL: required fields and VERIFIED-only gate implemented; all malformed-input cases NOT RUN. |
| R-04 | Execute is blocked until policy gates pass. | Attempt execution before evidence/approval gates; verify no side effect is invoked. | Test output plus safe adapter. | PASS in local core test: execution authorization is gated and invocation_performed=false. |
| R-05 | Tool routing does not imply invocation or permission. | Route to a registered-but-unavailable tool; ensure no invocation is claimed. | Adapter registry and test output. | PARTIAL: core explicitly does not invoke adapters; real adapter registry/routing is not implemented. |
| R-06 | Side effects are idempotent where possible. | Replay the same idempotency key; verify one logical authorization; reject changed arguments. | Persistent idempotency record and test. | PASS for authorization idempotency in local core tests; external side-effect idempotency NOT RUN. |
| R-07 | State survives restart and can recover from a checkpoint. | Restart DB client, read state, restore checkpoint, and ensure approval resets without replay. | Before/after state and audit. | PASS for local SQLite persistence/checkpoint recovery tests; process restart/deployed storage NOT RUN. |
| R-08 | Audit history is append-only and secrets are redacted. | Execute success/failure paths; inspect records for events and secret-shaped values. | Audit assertions and redaction test. | PARTIAL: audit writes and common-string redaction tested; tamper resistance and broader redaction corpus NOT RUN. |
| R-09 | Errors are captured and safely retried. | Inject timeout, validation failure, stale state, and storage failure; avoid unsafe blind retry. | Failure-path tests and error ledger. | PARTIAL: permission denial and UNKNOWN_OUTCOME blocking tested; timeout/storage failure NOT RUN. |
| R-10 | Budget, rate limit, timeout, and retry policy are explicit. | Simulate limit exhaustion and timeout; verify bounded handling and clear status. | Configuration plus deterministic tests. | NOT RUN. |
| R-11 | OpenAI integration follows current schemas and permissions. | Validate request/tool schema against current docs and an authorized test project. | Request/response fixtures and account evidence. | PARTIAL: relevant official sections reviewed; no API request run and no authorized API project checked. |
| R-12 | ChatGPT app/connector setup is actually supported. | Connect a test app/server in intended account and exercise read-only tool first. | Host logs and connection evidence. | NOT RUN. |
| R-13 | ChatGPT Mobile behavior is verified separately. | Test discovery, connection, read, write approval, and failure display in actual mobile app/account. | Dated client/version test record. | NOT RUN; mobile-only capability remains UNKNOWN. |
| R-14 | Branch changes are isolated and reviewable. | Compare working branch with source branch and main separately; inspect changed paths. | GitHub compare and file list. | PASS for source-branch comparison: project-local files only; comparison against main has inherited/older changes and is tracked separately. |
| R-15 | Delivery claims match evidence. | Map every requirement to PASS/PARTIAL/UNKNOWN/BLOCKED/NOT RUN and name test environment. | Final acceptance report and test output. | NOT RUN; final acceptance review remains open. |

## Local test evidence
- Command run in the development worktree: `python -m py_compile runtime/control_plane.py runtime/mcp_server.py` and `python -m unittest discover -v`.
- Result: 10 tests passed, 0 failed.
- Coverage: health/unique IDs, VERIFIED evidence gate, execution authorization without invocation, permission-denial audit, idempotency/reuse mismatch, restart persistence, checkpoint recovery with approval reset, final verification reference, UNKNOWN_OUTCOME blocking, and secret-shaped string redaction.
- Limitation: the local environment did not have the MCP Python SDK installed. The adapter import, MCP protocol, Streamable HTTP transport, and ChatGPT host integration were NOT RUN. The tests were run against the development worktree core; GitHub branch files were separately read back and their blob SHAs recorded.

## Proposed verification levels
1. Static: schemas, state machine, permissions, and dependency inspection.
2. Unit: deterministic policy/state/idempotency/redaction tests.
3. Integration: database restart/recovery, MCP adapter, and real adapter tests.
4. Failure-path: timeout, malformed payload, duplicate request, unavailable tool, denied permission, and persistence failure.
5. Host: actual ChatGPT connection and tool invocation in the target account.
6. Mobile: actual iOS/Android client behavior; do not infer this from API tests.
7. Release review: compare branch diffs, verify no secret leakage, and document unsupported capabilities.

## Stop conditions
- Stop and report BLOCKED if the target branch, required permission, or test environment cannot be established.
- Do not bypass authentication, approval, rate limits, or host security controls to obtain a PASS.
- If a write or ingestion call warns/errors, inspect the exact response, reduce only structurally safe payload size, and read back after each successful write.
- Never mark a requirement PASS based only on a search result, source inspection, or unexecuted test plan.
- Accumulate ordinary errors for milestone 10 review; raise urgent security/privacy risks immediately.

## Architecture decision gate
- A provisional architecture is recorded in ARCHITECTURE_DECISION.md: ChatGPT Apps SDK + MCP control backend is the preferred conditional path; Responses API with custom UI is a fallback; existing private plugins are not reused until deliberately selected.
- The remote write-capable server remains BLOCKED until authentication, TLS, least privilege, approval policy, and secrets management are configured and tested.
- Mobile/account support remains UNKNOWN until tested in the intended account/client.
