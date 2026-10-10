# Evidence Register
Project: IRIS Platform-First Control
Last checked: 2026-10-11
Rule: search result discovery is evidence of a source's existence and advertised scope, not proof that a capability works in this account or mobile client. Re-open and review full source before implementation.

| ID | Status | Claim supported | Official source | Retrieval date | Validation still required |
|---|---|---|---|---|---|
| E-001 | VERIFIED (source discovered) | OpenAI Responses API is a current API interface for model responses and supports tool use through documented APIs. | https://developers.openai.com/api/reference/responses/overview/ ; https://developers.openai.com/api/docs/guides/tools | 2026-10-11 | Read current schema, auth, tool definitions, state/retention, rate limits, and test with an authorized API account before selecting implementation. |
| E-002 | VERIFIED (source discovered) | OpenAI Agents SDK documentation describes agent execution and includes tracing and guardrail concepts. | https://developers.openai.com/api/docs/guides/agents ; https://openai.github.io/openai-agents-python/tracing/ ; https://openai.github.io/openai-agents-python/guardrails/ | 2026-10-11 | Determine which capabilities are appropriate to reuse; do not assume SDK traces replace durable IRIS project records or deterministic policy gates. |
| E-003 | VERIFIED (source discovered) | OpenAI Apps SDK is based on MCP and supports building apps that connect tools/data to ChatGPT. | https://help.openai.com/en/articles/12515353-build-with-the-apps-sdk ; https://openai.com/index/introducing-apps-in-chatgpt/ | 2026-10-11 | Confirm current availability, plan/workspace permissions, deployment requirements, and whether target mobile client supports the intended interaction. |
| E-004 | VERIFIED (source discovered) | OpenAI documents building remote MCP servers for plugins and API integrations. | https://developers.openai.com/api/docs/mcp | 2026-10-11 | Confirm exact transport, authentication, approval semantics, endpoint requirements, and supported ChatGPT connection path. |
| E-005 | VERIFIED (GitHub connector) | Repository exists, default branch is main, and working branch ref exists. | https://github.com/Prasong1993/Prasong/tree/work/iris-control-renovation-20261011-copy | 2026-10-11 | Branch protection, Actions state, and local/runtime test capability have not been checked. |
| E-006 | UNKNOWN | All intended functions can be operated exclusively from ChatGPT mobile, without any external hosting or setup surface. | No sufficient evidence yet. | 2026-10-11 | Must not assume. Map each workflow to ChatGPT app support, remote server requirements, and account permissions. |
| E-007 | UNKNOWN | The complete system can be made “100% working”. | Not a testable claim until acceptance scope is defined. | 2026-10-11 | Replace with measurable acceptance criteria, supported environments, and test coverage. |

## Evidence policy
- Use official OpenAI documentation first for OpenAI/ChatGPT capabilities and constraints.
- Record exact claim, source URL, retrieval date, version/revision when available, affected design decision, and linked test.
- Distinguish source discovery from full source review, static inspection, and runtime verification.
- Recheck volatile platform/plan/feature availability before release.
- Never treat a search snippet or an inferred capability as a successful test.
