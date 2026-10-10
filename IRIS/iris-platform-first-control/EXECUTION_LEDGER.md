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
  5. Created IRIS/iris-platform-first-control/PROJECT_CHARTER.md on the working branch. GitHub returned commit 5650c5d1b53d5b4f1063888289457072b28ce29a.
  6. Created IRIS/iris-platform-first-control/EVIDENCE_REGISTER.md on the working branch. GitHub returned commit 65108e741dad4c9e38bc3307b52af52657d6ccca.
- Evidence:
  - Branch ref query returned commit SHA 27e211c7797860703c0af747c5280e8d02dae8ff before these new documentation commits.
  - Project charter and evidence register were created through GitHub's create-file API targeting the explicit working branch.
  - Official source URLs are recorded in EVIDENCE_REGISTER.md.
- Errors / recovery:
  - An initial GitHub fetch using an API URL encoding for the branch path was rejected as an invalid repository path. Recovered by fetching the GitHub tree URL and the Git ref endpoint; no repository content was changed by the failed read.
- Not run:
  - No Python/runtime code has been implemented or executed.
  - No unit/integration/E2E tests or GitHub Actions status have been checked.
  - No deployment or ChatGPT mobile runtime test has been performed.
  - No changes to main, merge, or pull request were made.
- Next:
  1. Review full official documentation and current platform restrictions.
  2. Inspect current branch and source files; compare branch against source branch.
  3. Derive requirements and test matrix before selecting a minimal architecture.

## Entry EX-0002 — 2026-10-11
- Status: VERIFIED for branch diff and persisted documentation; BLOCKED for full official-page extraction in this pass.
- Actions:
  1. Read back all three project files from the exact working branch; content and blob SHAs were returned.
  2. Compared working branch against work/iris-control-renovation-20261011. GitHub compare reported status ahead, ahead_by=3, behind_by=0, total_commits=3; the three changes are the three project documentation files listed above.
  3. Attempted to scrape full official documentation pages; the scraper rejected the request because its required formats parameter was not supplied. No external site or repository content was changed by this failed read.
- Errors / recovery:
  - Full-page scrape not recovered in this pass. Existing search results and official source URLs remain discovery-level evidence only; they must not be treated as complete technical review.
- Current verified scope:
  - Three project documents exist on the working branch and are readable.
  - Working branch contains three documentation commits ahead of the source branch and is not behind it at comparison time.
  - This compare does not prove the branch is unchanged relative to main, nor does it prove runtime correctness.
- Not run:
  - Implementation, tests, CI inspection, deployment, mobile-client validation, and permission/plan validation.

## Entry EX-0003 — 2026-10-11
- Status: VERIFIED for the updated charter write; read-back verification pending at the time of this entry.
- Request: adopt an integrated, cautious write workflow and recover from data-ingestion/write warnings by reducing the payload incrementally until the cause is resolved, specifically for writes.
- Action:
  1. Re-read PROJECT_CHARTER.md before changing it.
  2. Added a Write-safety and warning-recovery protocol to PROJECT_CHARTER.md on the explicit working branch.
  3. GitHub returned commit 3c63a095db7a465c08578608a8b0dd3045433c57 and content blob SHA f3c808c2bd3921e566e8ea88b6666bf115db7d94.
- Protocol captured:
  - inspect exact warning; don't blindly repeat the same request;
  - diagnose size/shape, encoding, stale SHA, permissions, branch/ref, rate-limit, or other cause;
  - reduce/split only where structurally safe, never discard required content or bypass controls;
  - read back after successful writes and record unresolved warnings as BLOCKED.
- Next verification: fetch PROJECT_CHARTER.md from the exact branch, confirm the protocol text is present, then compare the branch to the source branch.

## Entry EX-0004 — 2026-10-11
- Status: VERIFIED.
- Read-back: fetched PROJECT_CHARTER.md from work/iris-control-renovation-20261011-copy and confirmed the complete write-safety and warning-recovery protocol is present. Returned content blob SHA: f3c808c2bd3921e566e8ea88b6666bf115db7d94.
- Branch comparison: GitHub compare reports work/iris-control-renovation-20261011-copy ahead_by=6, behind_by=0 relative to work/iris-control-renovation-20261011. The reported changed-file set contains only PROJECT_CHARTER.md, EVIDENCE_REGISTER.md, and EXECUTION_LEDGER.md.
- Warnings during these writes: no GitHub write warning/error was returned. One earlier documentation scrape attempt failed due to a missing required parameter; this was a read/research failure, not a write warning, and is recorded in EX-0002.
- Limits: this verifies persisted documentation and branch comparison only; no application runtime or tests were run.
