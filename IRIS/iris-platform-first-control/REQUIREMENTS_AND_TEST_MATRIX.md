# Requirements and Test Matrix
Project: IRIS Platform-First Control
Status: Core implementation and local source-verifier tests exist; MCP host and mobile integration remain unverified.
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
| R-03 | Evidence is provenance-aware and cannot self-assert VERIFIED. | Submit incomplete/untrusted evidence; test allowlist, redirect, size, query, digest and failure paths. | Source retrieval receipt, content digest, and audit events. | PARTIAL: source fetch/digest tests pass; semantic claim verification and production DNS-pinning review remain NOT RUN. |
| R-04 | Execute is blocked until policy gates pass. | Attempt execution before verified source evidence/approval; verify no side effect is invoked. | Unit test and safe adapter. | PASS for core gate simulation; actual external adapter invocation is not implemented. |
| R-05 | Tool routing does not imply invocation or permission. | Ensure authorization does not claim invocation. | Adapter registry and test output. | PARTIAL: invocation_performed=false; actual adapter registry/routing not implemented. |
| R-06 | Side effects are idempotent where possible. | Replay an idempotency key and reject changed arguments. | Persistent idempotency record and test. | PASS for authorization idempotency; external side-effect idempotency NOT RUN. |
| R-07 | State survives restart and can recover from a checkpoint. | Reopen DB, restore checkpoint, reset approval, and do not replay side effects. | State and audit output. | PASS in local SQLite unit tests; deployed storage/restart NOT RUN. |
| R-08 | Audit history is append-only and secrets are redacted. | Inspect success/failure audit events and secret-shaped values. | Audit assertions and redaction test. | PARTIAL: append events and common-string redaction tested; tamper resistance/broader redaction corpus NOT RUN. |
| R-09 | Errors are captured and safely retried. | Inject denied permission, digest mismatch, unknown outcome, timeout, and storage failure. | Failure-path tests and ledger. | PARTIAL: permission denial, digest mismatch, and UNKNOWN_OUTCOME tested; timeout/storage failure NOT RUN. |
| R-10 | Budget, rate limit, timeout, and retry policy are explicit. | Simulate limit exhaustion and timeout; verify bounded handling. | Configuration and tests. | PARTIAL: source fetch timeout/body limits implemented; model/API budgets and full retry policy NOT RUN. |
| R-11 | OpenAI integration follows current schemas and permissions. | Validate request/tool schema and an authorized API test. | Request/response fixtures and account evidence. | PARTIAL: official docs reviewed; no API request or account permission test. |
| R-12 | ChatGPT app/connector setup is supported. | Connect a test app/server and exercise a read-only tool first. | Host logs and connection evidence. | NOT RUN. |
| R-13 | ChatGPT Mobile behavior is verified separately. | Test discovery, connection, read, write approval, and failures on the actual mobile client/account. | Dated client/version record. | NOT RUN; mobile-only capability UNKNOWN. |
| R-14 | Branch changes are isolated and reviewable. | Compare working branch with source branch and main separately. | GitHub compare and file list. | PASS relative to source branch: project-local paths only; main comparison includes older/inherited IRIS changes. |
| R-15 | Delivery claims match evidence. | Map every requirement to PASS/PARTIAL/UNKNOWN/BLOCKED/NOT RUN. | Final acceptance report. | NOT RUN; final acceptance review remains open. |
| R-17 | Journal data is bounded and branch use is controlled. | Verify input/output projection limits, compact history summaries, start/finish failure behavior, and source-branch read-back; verify no implicit database/runtime switch on Git ref change. | Exact-commit tests, journal read-back, and branch/diff evidence. | PARTIAL: bounded projection implemented in MCP adapter; exact-commit runtime tests NOT RUN. Branch-switch rules documented; no runtime switch is claimed. |
| R-16 | AI actions are recorded for reliable continuation. | Verify each IRIS MCP tool call writes a STARTED event before execution and a terminal event after it; failures are recorded; secret-shaped values are redacted; unfinished actions survive restart; resume returns task/checkpoint/audit/action history. | SQLite action journal, unit tests, actual MCP protocol call/read-back, and a CI run for the exact commit. | IMPLEMENTED IN WORKING BRANCH; latest action-journal changes await CI result/read-back. Not a record of hidden model reasoning or actions outside this adapter. |

## Local test evidence
- GitHub Actions command on Python 3.12.15: `python -m py_compile runtime/*.py tests/*.py` and `python -m unittest discover -v`.
- Verified CI baseline before the AI action-journal change: MCP SDK **2.3.0** installed; compile passed; **18 tests passed, 0 failed**, including real MCP stdio discovery and calls. Run: https://github.com/Prasong1993/Prasong/actions/runs/38102751491
- The action-journal implementation adds two tests; the exact post-change commit must complete CI before those changes can be called PASS.
- Coverage: health/IDs, UNKNOWN evidence gate, client self-assertion rejection, verifier digest mismatch audit, execution authorization without invocation, permission denial/audit, idempotency/reuse mismatch, restart persistence, checkpoint recovery with approval reset, final verification reference, UNKNOWN_OUTCOME blocking, secret redaction, allowlisted source retrieval/digest, disallowed host, query rejection, non-200/redirect rejection, and oversized body rejection.
- Limitation: the SDK/protocol baseline passed in GitHub Actions, but this does not test authenticated Streamable HTTP, live external source retrieval, DNS pinning, ChatGPT host integration, or Android behavior. Source-verifier unit tests use an injected fake fetcher; live external retrieval remains NOT RUN.

## Verification levels
1. Static: schemas, state machine, permissions, dependencies.
2. Unit: deterministic policy/state/idempotency/redaction/trusted-verifier boundary.
3. Integration: live source retrieval, database restart/recovery, MCP adapter, and actual adapter tests.
4. Failure-path: timeout, malformed payload, duplicate request, denied permission, digest mismatch, redirect, and persistence failure.
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
- The source verifier currently uses an exact hostname allowlist, HTTPS-only URLs, no query parameters/redirects, pre-fetch public-address checks, timeouts, and body-size limits. Review DNS pinning and deployment network policy before production.
- Mobile/account support remains UNKNOWN until tested in the intended account/client.


## Fresh SDK review — 2026-10-11
- Official SDK first-steps and migration documentation reviewed: https://py.sdk.modelcontextprotocol.io/get-started/first-steps/ and https://py.sdk.modelcontextprotocol.io/migration/
- The documented import `from mcp.server import MCPServer` matches runtime/mcp_server.py.
- Official documented development commands include `uv run mcp dev runtime/mcp_server.py` and `uv run mcp run runtime/mcp_server.py --transport streamable-http`; these are not production-readiness evidence.
- Adapter import/protocol behavior remains NOT RUN because the SDK has not been installed in the available runtime. The Streamable HTTP command must not be exposed publicly before authentication, TLS, least privilege, and deployment controls are implemented and tested.
- Current acceptance gaps remain: live network/DNS pinning tests, semantic claim verification, full transition/failure matrix, authenticated remote transport, target-account Apps SDK, and Android mobile integration.

## ChatGPT-first workspace rule
- The active ChatGPT conversation and tools available through this session are the primary work surface. Keep decisions, progress, action/recovery notes, and delivery here.
- Do not create or require a separate runtime or test workspace merely to increase complexity. GitHub is versioned project storage, not proof that ChatGPT itself is executing the project.
- PASS requires an observed result in the applicable current execution context. Code inspection, old CI, mocks, or a successful file write do not prove current runtime success.
- If this session cannot run Python tests, a live MCP handshake, target-account app connection, or Android E2E, mark that check NOT RUN/BLOCKED. Do not silently substitute another environment.
- On continuation, inspect the ledger/action records first and record action, tool/target, result/error, changed artifact, read-back, status, and next safe action. Unresolved actions must be reconciled before retrying.
