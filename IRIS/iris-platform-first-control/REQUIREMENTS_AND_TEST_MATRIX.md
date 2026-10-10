# Requirements and Test Matrix
Project: IRIS Platform-First Control
Status: Draft for internal design gate; no runtime implementation validated yet.
Date: 2026-10-11
Working branch: work/iris-control-renovation-20261011-copy

## Scope and boundaries
- ChatGPT/OpenAI is the preferred user and model platform, subject to actual account/client support.
- IRIS is a thin deterministic control plane for project state, task state, permissions, checkpoints, evidence, idempotency, and audit.
- Reuse supported OpenAI capabilities where they fit. Do not recreate the model loop, tool orchestration, or tracing without a demonstrated gap.
- Do not modify main or merge this branch as part of this project.
- No API key, OAuth token, or secret may be committed or copied into logs.

## Requirements and acceptance tests

| ID | Requirement | Acceptance test | Evidence required | Initial status |
|---|---|---|---|---|
| R-01 | Every task has stable project/task/correlation identifiers. | Create a task; verify IDs are unique, persisted, and returned on read-back. | DB/API output and audit row. | NOT RUN |
| R-02 | State transitions are deterministic and gated. | Attempt valid and invalid transitions; invalid transitions must fail without advancing state. | Test output plus persisted rejection event. | NOT RUN |
| R-03 | Evidence is provenance-aware. | Submit evidence with missing source, timestamp, digest, or invalid status; reject incomplete evidence. | Validation tests and evidence rows. | NOT RUN |
| R-04 | Execute is blocked until policy gates pass. | Attempt execution before evidence/approval gates; verify no side effect is invoked. | Tool-call spy or safe test adapter and audit log. | NOT RUN |
| R-05 | Tool routing does not imply invocation or permission. | Route to a registered-but-unavailable tool; ensure response says no invocation occurred. | Adapter registry and test output. | NOT RUN |
| R-06 | Side effects are idempotent where possible. | Replay the same idempotency key; verify one logical side effect and trace both attempts. | Persistent idempotency record and test. | NOT RUN |
| R-07 | State survives restart and can recover from a checkpoint. | Create checkpoint, restart runtime, read state, resume without inventing missing facts. | Before/after database snapshots and recovery audit. | NOT RUN |
| R-08 | Audit history is append-only and secrets are redacted. | Execute success and failure paths; inspect records for events and secret-like values. | Audit assertions and redaction test. | NOT RUN |
| R-09 | Errors are captured and safely retried. | Inject timeout, validation failure, stale state, and storage failure; verify no unsafe blind retry. | Failure-path tests and error ledger. | NOT RUN |
| R-10 | Budget, rate limit, timeout, and retry policy are explicit. | Simulate limit exhaustion and timeout; verify bounded handling and clear status. | Configuration plus deterministic tests. | NOT RUN |
| R-11 | OpenAI integration follows current schemas and permissions. | Validate request/tool schema against current official docs and an authorized test project. | Request/response fixtures and account-specific evidence. | NOT RUN |
| R-12 | ChatGPT app/connector setup is actually supported. | Connect a test app/server in the intended account and exercise read-only tool first. | Host logs, connection result, permission screen evidence. | NOT RUN |
| R-13 | ChatGPT Mobile behavior is verified separately. | On the actual mobile app/account, test discovery, connection, read, write approval, and failure display. | Dated client/version test record. | NOT RUN |
| R-14 | Branch changes are isolated and reviewable. | Compare working branch with its source branch and main separately; inspect every changed path. | GitHub compare results and file list. | PARTIAL: branch comparisons available; runtime files not yet created by this project. |
| R-15 | Delivery claims match evidence. | Final report maps every requirement to PASS/FAIL/UNKNOWN/BLOCKED/NOT RUN and names test environment. | Acceptance report and linked test output. | NOT RUN |

## Proposed verification levels
1. Static: schemas, state machine, permissions, and dependency inspection.
2. Unit: deterministic policy/state/idempotency/redaction tests.
3. Integration: database restart/recovery, API, MCP, and real adapter tests.
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

## Architecture decision gate (not yet approved)
Before coding, compare at least:
- A: ChatGPT Apps SDK + remote MCP backend + minimal durable control-plane store.
- B: OpenAI Responses API + custom application UI/backend.
- C: use existing ChatGPT plugin/connector capabilities plus a smaller state/evidence service.

For each option document mobile/account support, hosting, authentication, persistence, audit, cost/limits, implementation burden, and the tests needed. Select the smallest supported architecture that meets R-01 through R-15. Do not pick a database or framework solely because an older IRIS version used it.
