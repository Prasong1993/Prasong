# IRIS Platform-First Control — Project Charter
Date: 2026-10-11
Status: ACTIVE / evidence-first / implementation not yet validated end-to-end

## Mission
Build the next isolated IRIS Control iteration on the ChatGPT/OpenAI platform as the primary user workspace. Prefer existing OpenAI and ChatGPT capabilities; add only the minimum integration/control layer needed to coordinate large projects, preserve state, route work, and verify outcomes.

## Git boundary
- Repository: Prasong1993/Prasong
- Working branch: work/iris-control-renovation-20261011-copy
- Starting branch: work/iris-control-renovation-20261011
- Do not merge into main, edit main, or push changes to main as part of this project.
- Keep project evidence, decisions, execution records, and test results on this branch.
- Before any write, verify the target branch and inspect existing files. Do not overwrite existing material without reading it first.

## Product principles
1. ChatGPT is the primary interface and reasoning/work surface; IRIS is the small control plane, not a competing model or duplicate agent platform.
2. Reuse OpenAI/ChatGPT capabilities where they are available and supported; don't assume API capabilities automatically exist in the ChatGPT mobile app.
3. Minimize custom code. Build thin adapters, project state/evidence storage, policy gates, checkpoints, routing, and verification only where needed.
4. Capture each observable execution automatically where the available runtime permits: task, timestamp, branch/revision, inputs/outputs references, tools/actions, decision/gate results, errors, retries, and verification evidence. Never log secrets or unnecessary personal data. The AI must be able to inspect this record when resuming work instead of relying on conversational recall.
5. Separate VERIFIED, RECOVERED, UNKNOWN, BLOCKED, and NOT RUN. An UNKNOWN claim is not proof; static inspection is not runtime verification.
6. Errors and improvement proposals should be accumulated in the project record and summarized at the agreed review point (currently milestone 10), except urgent safety/security blockers that must be raised immediately.
7. No claim of “100% working” without a defined acceptance matrix and passing tests; report coverage and remaining limits explicitly.

## Initial architecture hypothesis (to validate before coding)
- ChatGPT / OpenAI surface: primary user interaction and model capability.
- IRIS control API: project/task identity, state machine, deterministic policy gates, checkpoints, idempotency, audit events.
- Evidence register: source URLs, retrieval date, version/claim, confidence/status, affected requirement/test, and last recheck.
- Tool adapters: only verified supported APIs/integrations, each with explicit permission and timeout/retry rules.
- Project storage: durable state and append-only execution/audit events; separate secrets from records.
- Verification: deterministic schema/state/policy checks plus targeted integration tests and recorded outcomes.

This is a hypothesis, not a final design. Choose storage, hosting, and integration method only after evidence and platform constraints are checked.

## Delivery gates
G0 Scope and branch verified.
G1 Official platform/API research recorded.
G2 Requirements and acceptance matrix agreed internally from supplied request; unresolved essential blockers documented.
G3 Minimal architecture and threat/permission model reviewed.
G4 Implementation on this branch only.
G5 Unit, integration, failure-path, idempotency, recovery, and audit tests run.
G6 Inspect actual branch diff and CI evidence; no merge to main.
G7 Final report states verified results, not-run tests, unknowns, and next steps.

## Acceptance criteria
- Project/task state is durable and traceable across sessions/restarts.
- Each meaningful action has a correlation/trace identifier and audit record.
- Each IRIS-routed AI tool action is journaled before execution and finalized after execution; interrupted actions remain visible as IN_PROGRESS/unknown until reconciled.
- A resume operation can recover task state, latest checkpoint, audit events, and recorded actions without inventing missing history.
- The journal records observable tool actions and outcomes, not hidden model reasoning or actions outside the IRIS adapter.
- Invalid transitions and policy violations are rejected deterministically before execution.
- Retries do not duplicate completed side effects where idempotency can be enforced.
- Tool permissions, timeouts, budget/rate limits, and failure handling are explicit.
- Recovery can resume from a checkpoint without silently inventing prior state.
- Evidence and test records link requirements to implementation and outcomes.
- ChatGPT remains the primary workflow surface; unsupported mobile or account features are clearly marked rather than assumed.

## Known limitation at project start
A GitHub branch and repository contents are accessible via the connected GitHub tool. This does not itself prove code execution, mobile ChatGPT availability, OpenAI account entitlement, or a working deployed endpoint. Those need separate tests/evidence.

## Write-safety and warning-recovery protocol
- Before writing, confirm repository, exact target branch, target path, current file content, and current blob SHA when updating.
- Use the smallest logical write that preserves file integrity. Prefer one file per commit for independent changes; do not split structured data in a way that leaves invalid or partial files.
- If the write tool or GitHub returns a warning/error, stop and inspect the exact response. Do not blindly retry the same payload.
- Diagnose whether the cause is payload size, invalid content/encoding, stale SHA, permissions, branch/ref, rate limits, or another API constraint.
- For payload-size or request-shape warnings, reduce the write incrementally: first remove nonessential bulk/formatting, then split into smaller complete files or valid appendable sections where supported. Re-read after each successful write. Do not drop required facts or weaken validation rules just to suppress a warning.
- If a warning persists or its cause is unclear, mark the write BLOCKED and record the exact warning and recovery attempts; do not claim success.
- After every successful write, read the exact path back from the target branch and verify the expected content/commit SHA. After related writes, compare branch diffs.
- This protocol governs data writes only; it does not authorize bypassing security, permission, size, rate-limit, or approval controls.
