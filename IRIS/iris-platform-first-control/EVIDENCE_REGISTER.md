# Evidence Register
Project: IRIS Platform-First Control
Last checked: 2026-10-11
Rule: source discovery is not proof of account access or host behavior. Record the exact claim and the level of inspection; test account-specific and mobile-specific behavior separately.

| ID | Status | Claim supported | Official source | Retrieval date | Validation still required |
|---|---|---|---|---|---|
| E-001 | VERIFIED (relevant sections reviewed) | Responses API supports model responses and tool use, including built-in tools, custom functions, and remote MCP connections. | https://developers.openai.com/api/docs/guides/migrate-to-responses ; https://developers.openai.com/api/docs/guides/tools | 2026-10-11 | Validate chosen request schema, model availability, authentication, rate limits, and cost using an authorized API project. |
| E-002 | VERIFIED (relevant sections reviewed) | Agents SDK can run agent loops and tools; official docs describe guardrails/human review, resumable results/state, and tracing/observability. | https://developers.openai.com/api/docs/guides/agents/sdk ; https://developers.openai.com/api/docs/guides/agents/guardrails-approvals ; https://developers.openai.com/api/docs/guides/agents-api/tracing | 2026-10-11 | Select only features that reduce custom code; SDK traces are not automatically a durable IRIS project ledger or deterministic policy engine. |
| E-003 | VERIFIED (relevant sections reviewed) | Apps SDK is based on MCP and can provide app logic and UI inside ChatGPT; current help article describes the SDK as preview and requires Developer Mode for testing. | https://help.openai.com/en/articles/12515353-build-with-the-apps-sdk ; https://openai.com/index/introducing-apps-in-chatgpt/ | 2026-10-11 | Confirm current account/workspace entitlement, app setup, publication requirements, and intended mobile-client behavior. |
| E-004 | VERIFIED (relevant sections reviewed) | OpenAI documents remote MCP servers and Secure MCP Tunnel; remote MCP can require an internet-accessible server and authentication, and tool approvals are configurable. | https://developers.openai.com/api/docs/guides/tools-connectors-mcp | 2026-10-11 | Confirm transport, authentication, approval policy, hosting, and the exact connection path available in the target ChatGPT account. |
| E-005 | VERIFIED (GitHub connector) | Repository Prasong1993/Prasong has default branch main and the named working branch exists. | https://github.com/Prasong1993/Prasong/tree/work/iris-control-renovation-20261011-copy | 2026-10-11 | Runtime, CI, branch protections, and deployment remain untested. |
| E-006 | UNKNOWN | All intended functions can be operated exclusively from ChatGPT mobile without external hosting or setup. | No sufficient evidence yet. | 2026-10-11 | Test actual account/client; do not infer mobile parity from general Apps SDK or API documentation. |
| E-007 | UNKNOWN | The complete system can be “100% working”. | Not a testable claim until scope and environment are defined. | 2026-10-11 | Use measurable acceptance criteria and report coverage and limits. |
| E-008 | VERIFIED (relevant sections reviewed) | Responses API supports stateful chaining/conversation mechanisms, but application-owned project state and audit durability still require an explicit design and retention policy. | https://developers.openai.com/api/docs/guides/migrate-to-responses ; https://developers.openai.com/api/docs/guides/your-data | 2026-10-11 | Choose durable storage, export/recovery format, retention, deletion, and data-minimization rules. |
| E-009 | VERIFIED (relevant sections reviewed) | Function calling is a request/response loop: the application receives a tool call and executes the function; a model proposal alone is not execution or authorization. | https://developers.openai.com/api/docs/guides/function-calling | 2026-10-11 | Validate arguments, authorize each action server-side, enforce idempotency and deterministic policy gates, and record tool result evidence. |
| E-010 | VERIFIED (relevant sections reviewed) | Remote MCP calls can require approval; OpenAI recommends reviewing/logging data shared with connectors and using trusted servers. | https://developers.openai.com/api/docs/guides/tools-connectors-mcp | 2026-10-11 | Define least privilege, approval levels, secret handling, timeouts, retry policy, and audit redaction. |
| E-011 | VERIFIED (relevant sections reviewed) | API keys must not be exposed in client code or public repositories; official production guidance recommends secure secret storage and key rotation. | https://developers.openai.com/api/docs/guides/production-best-practices | 2026-10-11 | Select hosting/secret management and verify no secrets enter logs, Git, or client bundles. |

## Design implications (evidence-linked)
1. Keep ChatGPT/OpenAI as the primary interface where the target account supports it; treat API integrations as separately hosted capabilities, not as automatic features of the mobile app. (E-001, E-003, E-006)
2. Prefer a thin deterministic control plane for project/task identity, policy decisions, checkpoints, idempotency, durable evidence, and recovery; do not recreate model reasoning, tool loops, or tracing unnecessarily. (E-001, E-002, E-008, E-009)
3. Treat tool proposals and registered capabilities as declarations only. Execute only through a real authorized adapter after server-side validation. (E-009, E-010)
4. Keep secrets outside source control and execution records; store only the minimum evidence needed for audit and recovery. (E-008, E-011)
5. Mobile-only support and account permissions remain UNKNOWN until tested on the actual target client/account. (E-003, E-006)

## Evidence policy
- Prefer current official OpenAI documentation for platform capabilities and constraints.
- Record the claim, source URL, retrieval date, affected decision, and linked acceptance test.
- Distinguish source discovery, relevant-section review, static inspection, automated tests, live runtime verification, and target-host/mobile verification.
- Recheck volatile platform, plan, and feature availability before release.
- Never treat search snippets, an SDK feature, or a successful source read as proof of working runtime behavior.
