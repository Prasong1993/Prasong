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
- Initial safety semantics:
  - Only VERIFIED evidence unlocks the initial plan/execution gates.
  - Permission denial is persisted to audit without advancing execution.
  - Authorization explicitly returns invocation_performed=false; it does not call external tools.
  - Idempotency key reuse with different arguments is rejected.
  - UNKNOWN_OUTCOME moves a task to BLOCKED; checkpoint recovery resets approval and does not replay an in-flight side effect.
  - Audit payloads redact common secret-shaped values.
- Local test evidence at that time:
  - Ran `python -m py_compile runtime/control_plane.py runtime/mcp_server.py` and `python -m unittest discover -v` in the development worktree.
  - Result: 10 tests passed, 0 failed before trusted-evidence hardening.
  - Limitation: the local environment did not have the `mcp` Python package installed. The MCP adapter's import, SDK schema generation, Streamable HTTP behavior, and ChatGPT host connection were NOT RUN.
- Official MCP SDK research:
  - Official SDK README and tutorial reviewed: https://github.com/modelcontextprotocol/python-sdk/blob/main/README.md and https://github.com/modelcontextprotocol/python-sdk/blob/main/docs_src/index/tutorial001.py
  - Official docs: https://py.sdk.modelcontextprotocol.io/get-started/
  - PyPI metadata reported MCP SDK 2.3.0 released 2026-10-02: https://pypi.org/project/mcp/
  - requirements.txt was aligned to `mcp[cli]>=2.3.0,<3.0.0`. Actual installation/import is still NOT RUN.
- Source read-back at that time: runtime/control_plane.py SHA 239dfcf30396d0992e0cb9b6258bacd8f9378144; runtime/mcp_server.py SHA 9e860c55238463079a92f3d5799f11e6731f4254; tests/test_control_plane.py SHA cce5864eaa80a666be55b66cb814e6476f1454de; README SHA 60d28d02e04b2b66d77413294a83eb914d78cbfc; ARCHITECTURE_DECISION.md SHA c19e695a14de095bc2bfb59ecd904bb2f8057357.
- Public exposure was already marked BLOCKED pending authentication, TLS, least privilege, approval policy, and secret management.

## Entry EX-0007 — 2026-10-11
- Status: VERIFIED for requirements-matrix read-back and branch comparisons; NOT RUN for host integration.
- Matrix initially mapped the first 10 local core tests to acceptance criteria; its read-back was verified.
- Comparison against source branch work/iris-control-renovation-20261011:
  - status ahead, ahead_by=23, behind_by=0 at that point.
  - reported changed paths were exclusively under IRIS/iris-platform-first-control/ (12 project-local paths).
- Separate comparison against main:
  - status ahead, ahead_by=49, behind_by=0 at that point.
  - comparison includes older/inherited IRIS/iris-controller-v0.6.5 changes as well as the new project. This is not a clean three-file diff relative to main.
- Account/mobile support, MCP SDK installation, CI, and deployment remained NOT RUN.

## Entry EX-0008 — 2026-10-11
- Status: RECOVERED after a security design issue was identified; 12 local core/trusted-boundary tests PASS; MCP SDK/host tests remain NOT RUN.
- Security issue found during review:
  - The first MCP adapter accepted a caller-supplied `status="VERIFIED"`. That would allow the caller/model to label its own evidence as verified without a trusted verification step.
  - This was caught before public deployment. No live remote service was exposed by this implementation.
- Corrective change:
  1. Added runtime/verified_control_plane.py. Its public evidence intake rejects VERIFIED supplied by the caller. The internal mark_evidence_verified method checks the observed content digest and records verifier identity/reference; it is deliberately not exposed as an MCP tool.
  2. Changed runtime/mcp_server.py so the MCP add_evidence tool always stores incoming evidence as UNKNOWN and does not accept a status parameter.
  3. Changed the trusted-verifier mismatch path so its failure audit event commits before the policy error is returned.
  4. Updated tests to assert client self-verification is rejected and a digest mismatch is audited.
  5. Updated README.md and REQUIREMENTS_AND_TEST_MATRIX.md to state that a real source-fetch/verification adapter is not yet implemented; until then, incoming MCP evidence cannot unlock execution.
- Error/recovery:
  - The first local test run after applying the new boundary failed because the local test helper still called the old direct VERIFIED path and one test helper name did not match the revised tests. This was a test-harness adaptation issue. The helper and local adapter stub were corrected, then the full local suite passed.
  - A package installation/version check was attempted with pip, but DNS/network access to PyPI was unavailable in the local environment. No repeated install attempt was made; SDK install/import remains NOT RUN.
- Latest local verification:
  - `python -m py_compile runtime/control_plane.py runtime/verified_control_plane.py runtime/mcp_server.py`
  - `python -m unittest discover -v`
  - Result: 12 tests passed, 0 failed. The suite covers health/IDs, UNKNOWN evidence gating, client self-assertion rejection, verifier digest mismatch audit, execution authorization without invocation, permission denial audit, idempotency, restart persistence, checkpoint recovery with approval reset, final verification reference, UNKNOWN_OUTCOME blocking, and secret-shaped redaction.
- Persisted source read-back:
  - runtime/verified_control_plane.py SHA: c41ef3898cb1d06c23ace260374840ebecf62661
  - runtime/mcp_server.py SHA after evidence-boundary change: 90366ec49d7cc0b8326d2c7edfe027ce4505f0c2
  - tests/test_control_plane.py SHA after trusted-boundary tests: 215e0deed9db684ddaaed37a15886e4dd7a0401a
  - README.md SHA after blocker documentation: 8ae0856516acff5369b30d02bae34415318502a7
  - REQUIREMENTS_AND_TEST_MATRIX.md SHA after status update: b29f29b1be45638f23a5f88692ff3140070460e8
- Remaining blockers:
  1. Trusted source-fetch/verification adapter is NOT IMPLEMENTED. MCP intake remains UNKNOWN-only, intentionally fail-closed.
  2. MCP SDK 2.3.0 cannot be installed in the current local environment; adapter import and protocol tests remain NOT RUN.
  3. No authenticated remote transport or hosting configuration has been established. Public deployment remains BLOCKED.
  4. Apps SDK Developer Mode, API credentials/entitlements, ChatGPT connection, and target mobile behavior are NOT RUN / UNKNOWN.
- Next:
  1. Implement a trusted source retrieval/verification adapter with SSRF protections, redirect checks, timeouts, size limits, and an explicit source policy.
  2. Install and test MCP SDK 2.3.0 in a permitted environment or authorized CI runner.
  3. Implement/configure authentication and authorization at the MCP transport boundary before remote exposure.
  4. Verify target-account Apps SDK availability and mobile behavior; then run host-level acceptance tests.
