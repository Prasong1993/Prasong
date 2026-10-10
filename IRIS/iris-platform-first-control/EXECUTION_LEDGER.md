# Execution Ledger
Project: IRIS Platform-First Control
Branch: work/iris-control-renovation-20261011-copy
Started: 2026-10-11
Purpose: preserve a reviewable record of actual work. Append entries; do not rewrite history to hide failures.

## Entry EX-0001 — 2026-10-11
- Status: VERIFIED for repository/source writes; NOT RUN for application runtime.
- Actor: ChatGPT using connected GitHub and web-search tools.
- Actions:
  1. Queried repository metadata for Prasong1993/Prasong; default branch returned as main.
  2. Queried GitHub branch search and confirmed the named working branch was returned.
  3. Retrieved the working branch's IRIS directory tree; found existing iris-controller-v0.6.2 and iris-controller-v0.6.5 folders. These are background evidence only and have not been copied or edited by this project.
  4. Searched official OpenAI sources for Responses API/tool use, Agents SDK tracing/guardrails, ChatGPT Apps SDK, and MCP server integration.
  5. Created IRIS/iris-platform-first-control/PROJECT_CHARTER.md and EVIDENCE_REGISTER.md on the working branch.
- Errors / recovery:
  - An initial GitHub fetch using an API URL encoding for the branch path was rejected as an invalid repository path. Recovered by fetching the GitHub tree URL and the Git ref endpoint; no repository content was changed by the failed read.
- Not run: runtime, automated tests, CI, deployment, and mobile-client validation.

## Entry EX-0002 — 2026-10-11
- Status: VERIFIED for branch diff and persisted documentation; BLOCKED for full-page extraction at that time.
- Actions:
  1. Read back the project documents from the exact working branch.
  2. Compared working branch against work/iris-control-renovation-20261011; the branch was ahead and not behind, with only project documentation listed in that comparison.
  3. An earlier scrape failed because required `formats` was omitted. This was a research/read failure, not a repository write failure.
- Limit: this did not prove runtime correctness or a clean diff against main.

## Entry EX-0003 — 2026-10-11
- Status: VERIFIED for charter write and subsequent read-back.
- Action: Added a write-safety and warning-recovery protocol to PROJECT_CHARTER.md on the explicit working branch.
- Protocol: inspect warnings; diagnose payload, encoding, stale SHA, permission, branch/ref, or rate-limit causes; reduce only structurally safe payloads; read back after successful writes; never bypass security or discard required facts to silence a warning.

## Entry EX-0004 — 2026-10-11
- Status: VERIFIED.
- Read-back: the charter contains the full write-safety protocol.
- Comparison against source branch reported the project documents only at that time. No runtime tests had been run.

## Entry EX-0005 — 2026-10-11
- Status: VERIFIED for relevant official documentation sections, evidence-register update, and requirements-matrix creation; NOT RUN for implementation/runtime at that time.
- Official documentation sections reviewed:
  1. Responses API migration/benefits: https://developers.openai.com/api/docs/guides/migrate-to-responses
  2. Tools: https://developers.openai.com/api/docs/guides/tools
  3. Function calling flow: https://developers.openai.com/api/docs/guides/function-calling
  4. Agents SDK: https://developers.openai.com/api/docs/guides/agents/sdk
  5. Guardrails and human review: https://developers.openai.com/api/docs/guides/agents/guardrails-approvals
  6. Agents tracing: https://developers.openai.com/api/docs/guides/agents-api/tracing
  7. MCP servers: https://developers.openai.com/api/docs/guides/tools-connectors-mcp
  8. Apps SDK: https://help.openai.com/en/articles/12515353-build-with-the-apps-sdk
  9. API data guidance: https://developers.openai.com/api/docs/guides/your-data
  10. Production/key/rate-limit guidance: https://developers.openai.com/api/docs/guides/production-best-practices
- Findings: model tool-call proposals are not execution or authorization; tool execution is application-side. Apps SDK testing requires Developer Mode in the documented preview flow. Mobile/account access remains UNKNOWN until tested on the target host. API keys must remain outside source control.
- Updated EVIDENCE_REGISTER.md and created REQUIREMENTS_AND_TEST_MATRIX.md.
- Compared working branch with source branch: ahead_by=7, behind_by=0 at that time. Compared with main separately: ahead_by=33, behind_by=0; main comparison includes older/inherited IRIS paths and is not a clean three-document diff.
- Existing private plugin inventory: chatgpt-control-api v0.2.3, iris-step1 v0.1.0, iris-controller v0.6.19. Inventory was inspected, but no plugin was updated or duplicated because the new architecture has not selected a specific reusable plugin.
- Not run: implementation, tests, CI, deployment, ChatGPT connection/mobile, API credentials, and account/workspace entitlements.

## Entry EX-0006 — 2026-10-11
- Status: VERIFIED for provisional architecture record, core implementation write/read-back, and local core test run; NOT RUN for MCP adapter import/host behavior; BLOCKED for public deployment until authentication and hosting are configured.
- Architecture:
  - Created ARCHITECTURE_DECISION.md. Provisional first choice is ChatGPT Apps SDK + MCP with a thin deterministic control plane, conditional on account/mobile support. Responses API + custom UI is a fallback, not assumed to be the ChatGPT mobile app. Existing plugins are not reused until deliberately selected.
  - Threat/permission controls include server-side authorization, explicit approvals, idempotency, timeouts, secret redaction, append-only audit, and fail-closed gates.
- Code authored on the working branch:
  - runtime/control_plane.py — SQLite schema and deterministic project/task/evidence/checkpoint/audit/idempotency/policy operations.
  - runtime/mcp_server.py — MCP tool adapter for health, project/task, evidence, planning, approval, execution authorization, result recording, verification, checkpoint/recovery, and audit.
  - runtime/requirements.txt — MCP SDK dependency range.
  - runtime/__init__.py, tests/test_control_plane.py, tests/__init__.py, and README.md.
- Safety semantics implemented in the core:
  - Only VERIFIED evidence unlocks the initial plan/execution gates.
  - Permission denial is persisted to audit without advancing execution.
  - Authorization explicitly returns invocation_performed=false; it does not call external tools.
  - Idempotency key reuse with different arguments is rejected.
  - UNKNOWN_OUTCOME moves a task to BLOCKED; checkpoint recovery resets approval and does not replay an in-flight side effect.
  - Audit payloads redact common secret-shaped values.
- Local test evidence:
  - Ran `python -m py_compile runtime/control_plane.py runtime/mcp_server.py` and `python -m unittest discover -v` in the development worktree.
  - Result: 10 tests passed, 0 failed. Coverage includes evidence gating, permission denial/audit, idempotency, restart persistence, checkpoint recovery, final verification, unknown-outcome blocking, and redaction.
  - Limitation: the local environment did not have the `mcp` Python package installed. The MCP adapter's import, SDK schema generation, Streamable HTTP behavior, and ChatGPT host connection were NOT RUN. The local unit tests exercise the core implementation; persisted GitHub source was separately read back and blob SHAs recorded.
- Official MCP SDK research:
  - Official SDK README and tutorial reviewed: https://github.com/modelcontextprotocol/python-sdk/blob/main/README.md and https://github.com/modelcontextprotocol/python-sdk/blob/main/docs_src/index/tutorial001.py
  - Official docs: https://py.sdk.modelcontextprotocol.io/get-started/
  - PyPI metadata reported MCP SDK 2.3.0 released 2026-10-02: https://pypi.org/project/mcp/
  - requirements.txt was aligned to `mcp[cli]>=2.3.0,<3.0.0`. Actual installation/import is still NOT RUN.
- Persisted source read-back:
  - runtime/control_plane.py blob SHA: 239dfcf30396d0992e0cb9b6258bacd8f9378144
  - runtime/mcp_server.py blob SHA: 9e860c55238463079a92f3d5799f11e6731f4254
  - runtime/requirements.txt final blob SHA: 7c947255c112d7a8f4ada29618248512e631e3ff
  - tests/test_control_plane.py blob SHA: cce5864eaa80a666be55b66cb814e6476f1454de
  - README.md final blob SHA: 60d28d02e04b2b66d77413294a83eb914d78cbfc
  - ARCHITECTURE_DECISION.md blob SHA: c19e695a14de095bc2bfb59ecd904bb2f8057357
- Safety boundary: README explicitly blocks public exposure of write-capable MCP tools until transport authentication, TLS, least-privilege permissions, approval policy, and secret management are configured and tested.
- Not run: MCP SDK installation, MCP protocol tests, CI, deployment, API-account authentication, Apps SDK Developer Mode, ChatGPT Mobile integration, and live side-effect adapter tests.

## Entry EX-0007 — 2026-10-11
- Status: VERIFIED for final requirements-matrix read-back and post-code branch comparisons; NOT RUN for host integration.
- Updated REQUIREMENTS_AND_TEST_MATRIX.md to map individual requirements to local test evidence. Current result is a mixture of PASS/PARTIAL/NOT RUN; the matrix does not claim end-to-end completion.
- Final matrix read-back blob SHA: 14c398cfff78fbfe5b13d6697c16a4021d778f0e.
- Final comparison against source branch work/iris-control-renovation-20261011:
  - status ahead, ahead_by=23, behind_by=0.
  - reported changed paths are exclusively under IRIS/iris-platform-first-control/ (12 project-local paths); no other paths are listed in this comparison.
- Separate comparison against main:
  - status ahead, ahead_by=49, behind_by=0.
  - the compare includes older/inherited IRIS/iris-controller-v0.6.5 changes as well as the new project. Therefore this branch is not a clean three-file diff relative to main; do not merge it or claim only new project files differ from main.
- Source read-back verified: updated evidence register, ledger, README, requirements, runtime package marker, tests package marker, test matrix, and architecture decision. The exact persisted blob SHAs are recorded in this ledger where relevant.
- Remaining blockers:
  1. MCP SDK 2.3.0 is documented in the dependency range but is not installed in the available local runtime; adapter import/protocol tests remain NOT RUN.
  2. No authenticated remote transport or hosting configuration has been established. Public deployment remains BLOCKED.
  3. Apps SDK Developer Mode, API credentials/entitlements, ChatGPT connection, and target mobile behavior are NOT RUN / UNKNOWN.
  4. CI workflow paths checked by name were not found at the root paths queried; no CI status has been established.
- Next:
  1. Install and test the declared MCP SDK in a permitted environment, or use an authorized CI runner.
  2. Implement and test authentication/authorization at the MCP transport boundary before remote exposure.
  3. Verify target-account Apps SDK availability and mobile behavior.
  4. Only after those gates, deploy and run host-level acceptance tests; then produce the final release report.
