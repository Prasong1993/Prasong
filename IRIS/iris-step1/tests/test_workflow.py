import json
import pytest
from fastapi.testclient import TestClient
from runtime.main import app
from runtime.database import init_db
from runtime.task_queue import register_adapter, clear_adapters

@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("IRIS_STEP1_DB_PATH", str(tmp_path / "test.db"))
    init_db()
    clear_adapters()
    with TestClient(app) as c:
        yield c
    clear_adapters()

def make_task(client, kind="echo"):
    p = client.post("/projects", json={"name": "test-project"}).json()
    t = client.post(f"/projects/{p['id']}/tasks", json={"title": "task-one", "kind": kind, "input": {"x": 1}})
    assert t.status_code == 201
    return p, t.json()

def test_missing_adapter_is_blocked_and_not_executed(client):
    _, task = make_task(client, "missing")
    assert client.post(f"/tasks/{task['id']}/approve").status_code == 200
    response = client.post(f"/tasks/{task['id']}/execute")
    assert response.status_code == 409
    current = client.get(f"/tasks/{task['id']}").json()
    assert current["status"] == "BLOCKED"
    assert "not performed" in response.text

def test_successful_workflow_persists_result_evidence_and_audit(client):
    register_adapter("echo", lambda data: {"echo": data})
    _, task = make_task(client)
    assert client.post(f"/tasks/{task['id']}/approve").status_code == 200
    assert client.post(f"/tasks/{task['id']}/execute").json()["status"] == "COMPLETED"
    assert client.post(f"/tasks/{task['id']}/verify").json()["status"] == "VERIFIED"
    assert client.post(f"/tasks/{task['id']}/deliver").json()["status"] == "DELIVERED"
    assert client.get(f"/tasks/{task['id']}/evidence").json()[0]["kind"] == "ADAPTER_RESULT"
    actions = [x["action"] for x in client.get("/audit", params={"task_id": task["id"]}).json()]
    assert "TASK_APPROVED" in actions and "TASK_VERIFIED" in actions

def test_duplicate_active_task_rejected(client):
    p, _ = make_task(client)
    response = client.post(f"/projects/{p['id']}/tasks", json={"title": "TASK-ONE", "kind": "echo"})
    assert response.status_code == 409
    assert response.json()["detail"] == "DUPLICATE_ACTIVE_TASK"

def test_invalid_transition_rejected(client):
    _, task = make_task(client)
    response = client.post(f"/tasks/{task['id']}/deliver")
    assert response.status_code == 409
