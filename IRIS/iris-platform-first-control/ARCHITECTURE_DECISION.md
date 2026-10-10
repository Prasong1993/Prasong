# Architecture Decision Record
Project: IRIS Platform-First Control
Date: 2026-10-11
Status: PROVISIONAL — implementation may proceed against the minimal backend contract; ChatGPT account/mobile integration is a separate release gate.

## Decision question
How should IRIS add project control, durable state, deterministic policy, checkpoints, and audit while reusing ChatGPT/OpenAI instead of recreating an AI runtime?

## Options compared

| Option | What it reuses | Custom work | Advantages | Risks / unresolved gates | Decision |
|---|---|---|---|---|---|
| A. ChatGPT Apps SDK + MCP control backend | ChatGPT as user interface; MCP tools; OpenAI host approval mechanisms; optional Apps SDK UI | Thin MCP server, deterministic policy, durable project/evidence/audit store, tests, hosting/auth | Closest fit to ChatGPT-first goal; model reasoning stays in host; one explicit control boundary | Developer Mode/account access, server hosting, auth, and target mobile support must be tested. Apps SDK article currently describes preview. | Preferred conditional path |
| B. Responses API + custom application | Responses API, built-in/custom tools, optional Agents SDK and tracing | Custom UI/backend, API credentials, model/tool loop, persistence, control policy | Explicit API control and testability; useful if the product must be a standalone app | Duplicates more host experience; API availability does not make it operate inside ChatGPT mobile; API usage/cost and key custody required | Fallback only if A is unavailable or requirements need a separate app |
| C. Existing plugin/controller integration + small evidence store | Existing private plugins and current connector capabilities | Reconcile overlap, durable evidence store, adapter tests | Potentially fastest if a specific existing plugin is proven suitable | Multiple overlapping IRIS plugins exist; reusing one could import legacy assumptions and duplicate state. Actual intended plugin not selected. | Do not adopt until source review proves a specific component can be reused cleanly |

## Selected provisional architecture
1. **Host surface:** ChatGPT/Apps SDK + MCP is the intended first integration, conditional on account and mobile verification. No claim of mobile support is made yet.
2. **Control service:** a small Python MCP service exposes task/project state operations and deterministic gates. It does not call a model or pretend a route is an invocation.
3. **Persistence:** a durable local/server-side database for project/task records, evidence references, checkpoints, idempotency keys, and append-only audit events. Exact database and hosting are selected only after concurrency, backup, and deployment requirements are confirmed; start with the smallest testable option.
4. **Policy:** pure deterministic checks in the control service; no model judgment may override a failed policy gate.
5. **Evidence:** store source URL, retrieval timestamp, content digest/reference, status, affected requirement, and test linkage. Avoid storing secrets or unnecessary raw personal data.
6. **Execution:** only explicit authorized adapters can perform side effects. Tool registry entries are metadata, not permissions. Each adapter declares permission, timeout, retry, idempotency, and audit behavior.
7. **Observability:** use OpenAI/Agents tracing only if the chosen runtime actually uses the Agents SDK. IRIS keeps its own durable ledger because traces and application audit serve different purposes.
8. **Client/API boundary:** API keys remain server-side. ChatGPT account auth, MCP OAuth, and OpenAI API authentication are separate identities and must not be conflated.

## Threat and permission model
- **Assets:** project state, source evidence, execution history, user data, provider credentials, external side effects.
- **Trust boundaries:** user/ChatGPT host → MCP/API transport → IRIS policy layer → adapter → external system; database and logs are separate storage boundaries.
- **Threats:** prompt-injection content in sources; forged/stale task IDs; unauthorized tool invocation; duplicate retries; secret leakage; audit tampering; partial persistence failures; unsupported host behavior.
- **Controls:** validate schemas and ownership on every request; allowlist transitions; server-side authorization; explicit approval for risky writes; least-privilege adapter credentials; idempotency keys; bounded timeouts/retries; secret redaction; append-only events; database transactions; tested backup/recovery; no execution on missing/UNKNOWN evidence.
- **Fail-closed rules:** reject invalid transitions, missing required evidence, denied permissions, expired approvals, stale revisions, or unavailable durable storage for actions that require auditability. Read-only evidence gathering may continue independently when safe.
- **Error policy:** preserve the original failure and each recovery attempt; do not retry an uncertain non-idempotent action. Raise urgent security/privacy blockers immediately; aggregate ordinary errors for milestone 10 review.

## Architecture gate and implementation sequence
- G0 — Branch and scope verified.
- G1 — Official platform sections reviewed; mobile/account entitlements remain UNKNOWN.
- G2 — Requirements/test matrix recorded.
- G3 — This architecture is a provisional decision; confirm no legacy plugin is required and no account entitlement is assumed.
- G4 — Implement deterministic core and automated tests locally; keep ChatGPT-host integration behind an adapter.
- G5 — Run unit, failure-path, persistence/restart, idempotency, and audit tests.
- G6 — Inspect working-branch diff and run available CI; do not merge to main.
- G7 — Deploy only with explicit environment/permission setup; test actual ChatGPT connection and mobile client.
- G8 — Report acceptance status and unresolved limitations. A local test pass does not satisfy the host/mobile gate.

## Decision conditions
- If Apps SDK/MCP cannot be enabled for the target account, record the exact blocker and compare supported alternatives before switching architecture.
- If mobile support is not confirmed, report it as UNKNOWN and do not market the project as mobile-ready.
- Reuse an existing private plugin only after a deliberate selection and compatibility review; do not create a duplicate plugin merely to test Plugin Creator.
