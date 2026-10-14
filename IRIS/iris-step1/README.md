# iris-step1 — Source-first controller

Status: IMPLEMENTATION IN PROGRESS. This is a new, isolated source area; it does not replace the existing IRIS controller or update the Plugin Creator release.

## Scope
A small FastAPI + SQLite workflow controller with explicit approval, registered adapters, persisted task results, evidence records, and an append-only transition audit. It never executes arbitrary shell commands. If no adapter is registered for a task kind, execution is blocked and recorded as not executed.

## Local run
```sh
python -m pip install -r requirements.txt
uvicorn runtime.main:app --app-dir IRIS/iris-step1 --reload
pytest -q IRIS/iris-step1/tests
``

For running from this directory instead:
```sh
python -m pip install -r requirements.txt
uvicorn runtime.main:app --reload
pytest -q
``

## Workflow
`QUEUED → APPROVED → RUNNING → COMPLETED → VERIFIED → DELIVERED`
Failure states: `BLOCKED`, `FAILED`. Each transition is recorded in the audit log. Adapter registration is code-controlled; task input cannot select a Python import or shell command.

## API
- `GET /`, `GET /health`
- `POST /projects`, `GET /projects/{project_id}`
- `POST /projects/{project_id}/tasks`, `GET /tasks/{task_id}`
- `POST /tasks/{task_id}/approve`, `/execute`, `/verify`, `/deliver`, `/fail?reason=...`
- `GET /tasks/{task_id}/evidence`, `GET /audit`

## Known boundaries
This is a starter implementation, not proof of production readiness. No external plugin execution, authentication/authorization, multi-user isolation, or database migration from an existing IRIS schema is implemented. Use a dedicated database path. Tests must be run in the target environment before declaring the source accepted.
