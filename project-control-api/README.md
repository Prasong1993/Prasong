# Project Control API (local-first)

Standalone project, separate from IRIS. Policy and verification are deterministic Python code; no LLM calls are made inside policy or verification.

## Workflow

`CONCEPT → DESIGN → EXECUTE → RESULT → VERIFY`

A stage cannot advance without evidence recorded for the current stage. Completion requires evidence for all five stages, a valid SHA-256 chained audit log, matching evidence hashes and metadata, and legal replay of stage transitions. Completed runs are immutable through the API.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set PROJECT_CONTROL_KEY to a long random secret in .env; never commit the real value.
set -a; source .env; set +a
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Docs: `http://127.0.0.1:8000/docs`; health: `http://127.0.0.1:8000/_api/health`.

## API

`GET /_api/health` is public. `POST /_api/control` requires `X-Project-Control-Key`.

Actions: `list`, `create`, `detail`, `evidence`, `advance`, `verify`, `audit`.

Examples:

```json
{"action":"create","title":"Example","description":"Optional"}
{"action":"evidence","runId":"...","source":"verified-source","content":"evidence content"}
```

## Deployment note

This implementation is Python/FastAPI/SQLite, not a Cloudflare Worker. Render is used for online smoke-testing; SQLite persistence on a free ephemeral service is not production-safe. Before production use, attach persistent storage or migrate the database to a managed persistent database, and configure `PROJECT_CONTROL_KEY` as a secret.
