# IRIS Platform-First Control

A new, isolated control-plane implementation. ChatGPT/OpenAI remains the preferred interaction and model platform; this repository adds deterministic policy gates, durable task/evidence metadata, checkpoints, idempotency, and audit only where needed.

## Current verification status

- Deterministic SQLite core: implemented and locally unit-tested in the development workspace.
- Trusted source verifier: implemented in `runtime/source_verifier.py`. It fetches only allowlisted HTTPS hosts, rejects query parameters and redirects, checks public DNS results for live fetches, enforces a timeout and body-size limit, and records only the content digest/provenance. **VERIFIED means source retrieval and digest integrity only; it does not prove the semantic truth of the claim.**
- MCP adapter: GitHub Actions Run #25 passed for code commit `77ff0f0cab00831c71dcb1be908bf90300298a8a` (Python compile, dependency installation/version recording, unit/failure-path tests, and MCP stdio protocol tests). Run: https://github.com/Prasong1993/Prasong/actions/runs/38103781519. Authenticated remote transport, live ChatGPT host behavior, and Android behavior remain **NOT RUN**. GitHub showed step pass states, but console logs required sign-in and were not independently inspected.
- ChatGPT Apps SDK/account/mobile connection: **NOT RUN**.
- Public deployment: **BLOCKED** until authenticated transport, least-privilege permissions, and hosting are configured and tested.

## Primary operating surface

The intended operator workspace is the active ChatGPT conversation and the tools actually available through that session. Keep decisions, progress, action records, recovery, and delivery here. GitHub is versioned storage for the project when required; it is not the runtime where ChatGPT itself is assumed to execute.

Do not require a separate shell, virtual environment, external server, deployment, or second test workspace merely to make routine work more complicated. Run only checks that can actually be performed through the current ChatGPT session and available tools. If the current session cannot run a Python test suite or a live MCP protocol handshake, report that specific test as NOT RUN; do not infer PASS from reading code, a mock, or an old CI run.

## Test and MCP boundary

The Python unit-test suite, failure-path tests, compilation, and MCP stdio protocol tests were executed by GitHub Actions Run #25 for code commit `77ff0f0cab00831c71dcb1be908bf90300298a8a`; all displayed steps passed. This validates that code commit only, not later commits, authenticated remote transport, the ChatGPT host, or Android. The current ChatGPT session did not itself execute Python. Do not expose write-capable MCP tools publicly without a supported authentication flow, TLS, least-privilege permissions, approval policy, and secret management.


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

## Journal payload limits and use conditions

- The MCP adapter writes a `STARTED` record before invoking a tool and a terminal record afterward. If the start record cannot be persisted, the operation is not invoked. If the final record cannot be persisted, treat the result as `UNKNOWN_OUTCOME` and inspect task state/history before retrying.
- Journal payloads are metadata, not a complete archive of arbitrary tool output: strings are capped at 500 characters, nested structures are depth-limited, dictionaries are capped at 30 keys, list samples are capped at 10 items, and history-reading tools store compact summaries to prevent recursive log growth. The caller still receives the normal tool result.
- Redaction is defense-in-depth, not a guarantee against every secret or personal-data format. Never send credentials, access tokens, passwords, or unnecessary personal data to tools.
- `session_id` is currently process-scoped, not a verified ChatGPT conversation ID; caller identity is unauthenticated in the local stdio adapter. Do not use these fields as proof of authenticated identity.
- The SQLite database is persistent only at the configured `IRIS_DB_PATH` and on storage that survives process restarts. A different path or separate deployment may use a different database. Back up and protect the database; do not assume Git branch changes migrate or switch database contents.

## Branch switching is not database switching

- Active source branch for this work: `work/iris-control-renovation-20261011-copy`. `main` remains read-only for this project until explicit approval.
- To test or continue work on the secondary branch, select that exact branch/ref in GitHub and read back the latest commit and files before editing.
- To switch to `main`, inspect the diff and acceptance status first; do not merge or write to `main` without explicit approval. Switching a Git ref changes the source revision only. It does not switch the running MCP process, install a server into ChatGPT, migrate the SQLite database, or prove a live connection.
- A runtime may use only one checked-out source revision at a time unless separate, explicitly configured deployments exist. Do not mix files from branches or assume two branches share state.
- Safe use is currently limited to local/authorized test environments. Public write-capable deployment is blocked until authenticated transport, TLS, authorization, least privilege, secret handling, and recovery/failure-path tests are verified.


## Verification snapshot — 2026-10-11

- Latest observed code-test run: GitHub Actions **Run #25**, ID `38103781519`; branch `work/iris-control-renovation-20261011-copy`; code commit `77ff0f0cab00831c71dcb1be908bf90300298a8a`; conclusion **SUCCESS**.
- The `verify` job displayed passing steps for Python setup, MCP SDK/CLI install, runtime/SDK version recording, Python compilation, unit/failure-path tests, and MCP stdio protocol tests. Total run duration was 19 seconds; the verify job took 15 seconds.
- The six bounded-journal projection tests are included in the code commit covered by that run. Do not claim live ChatGPT action capture, authenticated HTTP transport, Android E2E, or production readiness from this CI result.
- The CI job page displayed a Node.js 20 deprecation warning and a notice that `ubuntu-latest` is scheduled to migrate to Ubuntu 26 beginning 2026-10-19. These are maintenance warnings, not test failures.
- Actual console log output was not inspectable because GitHub displayed “Sign in to view logs”; only the run conclusion and displayed step states were observed.
