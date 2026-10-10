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
- Comparison against source branch work/iris-control-renovation-20261011: ahead_by=23, behind_by=0 at that point; reported changed paths were exclusively under IRIS/iris-platform-first-control/.
- Separate comparison against main: ahead_by=49, behind_by=0 at that point; comparison includes older/inherited IRIS/iris-controller-v0.6.5 changes as well as the new project. This is not a clean three-file diff relative to main.
- Account/mobile support, MCP SDK installation, CI, and deployment remained NOT RUN.

## Entry EX-0008 — 2026-10-11
- Status: RECOVERED after a security design issue was identified; 12 local core/trusted-boundary tests PASS; MCP SDK/host tests remain NOT RUN.
- Security issue found during review: the first MCP adapter accepted a caller-supplied `status="VERIFIED"`, which could let the caller/model label its own evidence as verified. This was caught before public deployment; no live remote service was exposed.
- Corrective change:
  1. Added runtime/verified_control_plane.py. Its public evidence intake rejects VERIFIED supplied by the caller. The internal mark_evidence_verified method checks the observed content digest and records verifier identity/reference; it is deliberately not exposed as an MCP tool.
  2. Changed runtime/mcp_server.py so MCP evidence intake stores UNKNOWN and does not accept a status parameter.
  3. Changed the trusted-verifier mismatch path so its failure audit event commits before the policy error is returned.
  4. Updated tests to assert client self-verification is rejected and a digest mismatch is audited.
- Error/recovery:
  - The first local test run after applying the new boundary failed because the local test helper still called the old direct VERIFIED path and one helper name did not match the revised tests. This was a test-harness adaptation issue. The helper and local adapter stub were corrected, then the full local suite passed.
  - A package installation/version check was attempted with pip, but DNS/network access to PyPI was unavailable. No repeated install attempt was made; SDK install/import remains NOT RUN.
- Latest local verification at that time: `py_compile` succeeded and 12 tests passed, 0 failed.
- Persisted source read-back: runtime/verified_control_plane.py SHA c41ef3898cb1d06c23ace260374840ebecf62661; runtime/mcp_server.py SHA 90366ec49d7cc0b8326d2c7edfe027ce4505f0c2; tests/test_control_plane.py SHA 215e0deed9db684ddaaed37a15886e4dd7a0401a; README SHA 8ae0856516acff5369b30d02bae34415318502a7; matrix SHA b29f29b1be45638f23a5f88692ff3140070460e8.
- Remaining blockers at that time: source verifier NOT IMPLEMENTED; MCP SDK install/adapter tests NOT RUN; authenticated remote transport/hosting BLOCKED; Apps SDK/account/mobile NOT RUN / UNKNOWN.

## Entry EX-0009 — 2026-10-11
- Status: VERIFIED for local source-verifier unit tests and GitHub writes/read-backs; NOT RUN for live external source retrieval, MCP SDK, and ChatGPT host/mobile integration.
- Implemented runtime/source_verifier.py and routed the MCP add_evidence tool through it.
- Source-verifier behavior:
  - Exact hostname allowlist (default list includes official OpenAI/MCP documentation hosts and GitHub/PyPI).
  - HTTPS only; rejects userinfo, non-443 ports, query parameters, and IP literals.
  - For live fetches, checks DNS results are public; rejects redirects and non-200 responses; enforces timeout and maximum response size; accepts text/JSON/XML content types and UTF-8 bodies.
  - Stores only content digest/provenance; raw fetched body is not persisted.
  - Marks evidence VERIFIED only after server-side fetch and digest comparison succeed. The status means source retrieval/content integrity only, not semantic truth of the claim.
  - Fetch failures from a validated URL are recorded as BLOCKED evidence when possible.
- Tests added in tests/test_source_verifier.py with injected fake fetchers; no live external HTTP request is claimed as tested.
- Latest local test run: `py_compile` succeeded and 17 tests passed, 0 failed.
- Recovery of test duration: injected fake-fetch tests initially attempted DNS resolution and took several seconds. Changed DNS preflight to run only for the live fetcher; rerun completed in about 0.06 seconds with all 17 tests passing.
- Persisted source read-back at that time: runtime/source_verifier.py SHA f3fccbde34d93ace44fb7358e60369e76075984f; runtime/mcp_server.py SHA f0ebc696a2d5745a292dcd4c3c4d892fe04ffc21; tests/test_source_verifier.py SHA d5198320045f872bf52d4f0729152a334f44e37b; README SHA 4bffbc764de955b78b5da356750ec85f19ba2c16; matrix SHA f1b29df34b2049bd71742fa4094f4d86f59af067.
- Source-branch comparison at that time: ahead_by=36, behind_by=0, project-local paths only.
- Remaining blockers at that time: MCP SDK installation/protocol tests NOT RUN; authenticated remote transport/hosting BLOCKED; DNS pinning review needed; Apps SDK/account/mobile NOT RUN / UNKNOWN.

## Entry EX-0010 — 2026-10-11
- Status: VERIFIED for updated source-verifier failure audit, tests, and branch read-back; NOT RUN for live external network, MCP SDK, and ChatGPT host/mobile integration.
- Improvement:
  - Source verification failures are now recorded as SOURCE_VERIFICATION_FAILED audit events using only the host and reason, not the full URL. This avoids putting potentially sensitive query values into the audit trail.
  - Added a test asserting a disallowed host is rejected and audited.
- Latest local test result remains 17 passed, 0 failed after this audit change. The tests use fake fetchers; live external retrieval is NOT RUN.
- Latest persisted blob SHAs:
  - runtime/verified_control_plane.py: d5038b31da87c6e06fac8f6f19ac39303e1c6bfc
  - runtime/source_verifier.py: 18a22218cb06ab8ad8daf1a03974f4a3b767e354
  - runtime/mcp_server.py: f0ebc696a2d5745a292dcd4c3c4d892fe04ffc21
  - tests/test_source_verifier.py: ccc6d911b22aa67d45a41d075204a83ca7722af4
  - README.md: 4bffbc764de955b78b5da356750ec85f19ba2c16
  - REQUIREMENTS_AND_TEST_MATRIX.md: f1b29df34b2049bd71742fa4094f4d86f59af067
- Latest branch comparisons:
  - Against source branch work/iris-control-renovation-20261011: ahead_by=40, behind_by=0; changed paths exclusively under IRIS/iris-platform-first-control/ (15 files).
  - Against main: ahead_by=66, behind_by=0; comparison includes inherited/older IRIS v0.6.5 files as well as the new project. Do not merge or claim only project-local differences relative to main.
- Remaining blockers:
  1. MCP SDK 2.3.0 could not be installed because the local environment has no DNS/network access to PyPI; adapter import and protocol tests remain NOT RUN.
  2. No authenticated remote transport or hosting configuration has been established. Public deployment remains BLOCKED.
  3. DNS preflight is not DNS pinning; review network egress/DNS pinning controls before production.
  4. Apps SDK Developer Mode, API credentials/entitlements, ChatGPT connection, and target mobile behavior remain NOT RUN / UNKNOWN.
- Next:
  1. Verify MCP adapter imports and protocol schemas in an environment with MCP SDK 2.3.0 installed.
  2. Implement/configure authenticated MCP transport and least-privilege access before any remote deployment.
  3. Test live source retrieval in the authorized environment, including redirect, DNS, timeout, content-type, and body-size cases.
  4. Verify target-account Apps SDK availability and mobile behavior before calling the project host-ready.
