"""REST API layer tests via FastAPI TestClient."""
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runtime"))

import database  # noqa: E402
database.DB_PATH = Path(tempfile.mkdtemp()) / "iris_api_test.db"
database.init_db()

from main import app  # noqa: E402


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_root_health_structure(client):
    assert client.get("/").status_code == 200
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/structure").json()["status"] == "WORKING_STRUCTURE"


def test_full_workflow_delivered(client):
    client.post("/work", json={"id": "API-1", "title": "api full"})
    for i in [1, 2, 3, 4, 5]:
        r = client.post(f"/work/API-1/step/{i}", json={"expected": f"s{i}", "actual": f"s{i}"})
        assert r.status_code == 201
    r = client.post("/work/API-1/verify", json={"expected": "f", "actual": "f"})
    assert r.status_code == 201 and r.json()["status"] == "VERIFIED"
    j = client.get("/work/API-1").json()
    assert j["work"]["status"] == "DELIVERED"
    assert len(j["errors"]) >= 0
    assert len(j["checkpoints"]) > 0
    assert len(j["audit"]) > 0
    assert len(j["verifications"]) == 1


def test_skip_step_409(client):
    client.post("/work", json={"id": "API-2", "title": "skip"})
    assert client.post("/work/API-2/step/2", json={"expected": "x", "actual": "x"}).status_code == 409


def test_final_verify_mismatch_409_and_persisted(client):
    client.post("/work", json={"id": "API-3", "title": "mismatch"})
    for i in [1, 2, 3, 4, 5]:
        client.post(f"/work/API-3/step/{i}", json={"expected": f"e{i}", "actual": f"e{i}"})
    r = client.post("/work/API-3/verify", json={"expected": "A", "actual": "B"})
    assert r.status_code == 409
    j = client.get("/work/API-3").json()
    assert j["verifications"][-1]["status"] == "MISMATCH"
    assert j["work"]["status"] != "DELIVERED"


def test_duplicate_work_409(client):
    client.post("/work", json={"id": "API-4", "title": "first"})
    assert client.post("/work", json={"id": "API-4", "title": "second"}).status_code == 409


def test_evidence_endpoints(client):
    r = client.post("/evidence", json={"id": "EV-API-1", "status": "V", "topic": "t",
                                       "fact": "f", "source": "s", "verification_state": "V"})
    assert r.status_code == 201
    assert client.post("/evidence", json={"id": "EV-API-1", "status": "V", "topic": "t",
                                          "fact": "f", "source": "s", "verification_state": "V"}).status_code == 409
    assert len(client.get("/evidence").json()["items"]) >= 1


def test_nonexistent_work_404(client):
    assert client.get("/work/NOPE").status_code == 404
