# IRIS Plugin Structure v0.6.3

## Architecture

```text
ChatGPT Host
    │
    ▼
IRIS Plugin Manifest
    │
    ▼
IRIS Skill / Orchestration Contract
    │
    ├── INSPECT
    ├── PLAN
    ├── EXECUTE
    ├── VERIFY
    └── DELIVER
    │
    ▼
Execution Boundary
    │
    ├── MCP / connected tool (required for remote execution)
    ├── supported host/app binding
    └── local runtime when explicitly available
    │
    ▼
IRIS Runtime
    ├── main.py       API boundary
    ├── controller.py state machine + gates
    ├── model.py      workflow/state definitions
    ├── verify.py     verification primitive
    └── database.py   persistence
    │
    ▼
SQLite State
    ├── evidence
    ├── work_units
    ├── step_runs
    ├── errors
    ├── checkpoints
    ├── verifications
    └── audit_log
```

## Contract

`Skill → Execution Boundary → Runtime → State → Verification → Delivery`

The skill must never imply that Python files are callable merely because they are packaged. Runtime execution is proven only by an actual connected execution boundary and returned evidence.

## Acceptance gates

- Package structure: PASS
- Manifest + skill discovery: PASS
- Runtime source present: PASS
- Runtime connected to host: must be separately proven
- Five-stage E2E execution: must be separately proven
- Final delivery: only after `VERIFIED`
