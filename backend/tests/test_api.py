"""API contract tests: validation rules and CRUD behaviour."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID = {
    "name": "demo",
    "action_type": "mock_command",
    "action_target": "cleanup-temp-files",
    "schedule_type": "interval",
    "schedule_value": "60",
}


def test_create_and_list_task():
    r = client.post("/tasks", json=VALID)
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "demo"
    assert body["status"] == "active"
    assert body["next_run_at"] is not None

    r = client.get("/tasks")
    assert r.status_code == 200
    assert any(t["name"] == "demo" for t in r.json())


def test_rejects_bad_cron():
    r = client.post("/tasks", json={**VALID, "schedule_type": "cron",
                                    "schedule_value": "not a cron"})
    assert r.status_code == 422


def test_rejects_tiny_interval():
    r = client.post("/tasks", json={**VALID, "schedule_value": "5"})
    assert r.status_code == 422


def test_rejects_unknown_mock_command():
    r = client.post("/tasks", json={**VALID, "action_target": "rm -rf /"})
    assert r.status_code == 422   # also proof we never accept arbitrary commands


def test_rejects_non_url_http_target():
    r = client.post("/tasks", json={**VALID, "action_type": "http",
                                    "action_target": "ftp://evil"})
    assert r.status_code == 422


def test_pause_and_resume():
    task_id = client.post("/tasks", json=VALID).json()["id"]

    r = client.patch(f"/tasks/{task_id}", json={"status": "paused"})
    assert r.json()["status"] == "paused"

    r = client.patch(f"/tasks/{task_id}", json={"status": "active"})
    assert r.json()["status"] == "active"


def test_404s():
    assert client.get("/tasks/does-not-exist").status_code == 404
    assert client.patch("/tasks/does-not-exist", json={"name": "x"}).status_code == 404
    assert client.delete("/tasks/does-not-exist").status_code == 404


def test_delete_removes_task_and_history():
    task_id = client.post("/tasks", json=VALID).json()["id"]
    assert client.delete(f"/tasks/{task_id}").status_code == 204
    assert client.get(f"/tasks/{task_id}").status_code == 404


def test_next_runs_helper():
    task_id = client.post("/tasks", json={**VALID, "schedule_value": "60"}).json()["id"]
    r = client.get(f"/tasks/{task_id}/next-runs?count=3")
    assert r.status_code == 200
    runs = r.json()
    assert len(runs) == 3
