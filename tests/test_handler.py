"""Offline API contract tests; a fake repository makes AWS credentials unnecessary."""
import json
import uuid

import pytest

from taskplatform import handler
from taskplatform.domain import ApiError


class MemoryRepo:
    def __init__(self):
        self.records = {}
        self.events = []

    def _record(self, ident, task_id):
        task = self.records.get((ident.tenant, task_id))
        if not task or (not ident.admin and task["ownerId"] != ident.subject):
            raise ApiError(404, "not_found", "Task not found")
        return task

    def create(self, ident, props):
        task_id = str(uuid.uuid4())
        item = {"taskId": task_id, "title": props["title"], "description": props.get("description", ""),
                "ownerId": ident.subject, "status": props.get("status", "OPEN"), "version": 1}
        self.records[(ident.tenant, task_id)] = item
        self.events.append({"action": "CREATED", "tenant": ident.tenant, "taskId": task_id})
        return item

    def get(self, ident, task_id):
        return self._record(ident, task_id).copy()

    def list_tasks(self, ident, limit, cursor):
        data = [v.copy() for (tenant, _), v in self.records.items() if tenant == ident.tenant
                and (ident.admin or v["ownerId"] == ident.subject)]
        return {"items": data[:limit], "nextCursor": None}

    def update(self, ident, task_id, expected, props):
        task = self._record(ident, task_id)
        if task["version"] != expected:
            raise ApiError(409, "conflict", "Version conflict")
        task.update(props)
        task["version"] += 1
        self.events.append({"action": "UPDATED", "tenant": ident.tenant, "taskId": task_id})
        return task.copy()

    def delete(self, ident, task_id, expected):
        task = self._record(ident, task_id)
        if task["version"] != expected:
            raise ApiError(409, "conflict", "Version conflict")
        del self.records[(ident.tenant, task_id)]
        self.events.append({"action": "DELETED", "tenant": ident.tenant, "taskId": task_id})

    def list_audit(self, ident, limit, cursor):
        return {"items": [e for e in self.events if e["tenant"] == ident.tenant][:limit], "nextCursor": None}


@pytest.fixture
def repo(monkeypatch):
    r = MemoryRepo()
    monkeypatch.setattr(handler, "DynamoRepository", lambda: r)
    return r


def call(method, path, *, tenant="acme", subject="alice", role="member", params=None, body=None, auth=True):
    event = {"rawPath": path, "requestContext": {"http": {"method": method}},
             "queryStringParameters": params}
    if auth:
        event["requestContext"]["authorizer"] = {"jwt": {"claims": {
            "custom:tenant_id": tenant, "custom:role": role, "sub": subject
        }}}
    if body is not None:
        event["body"] = json.dumps(body)
    result = handler.lambda_handler(event)
    return result["statusCode"], json.loads(result["body"]) if result["body"] else None


def test_health_public_and_private_routes_fail_closed(repo):
    assert call("GET", "/health", auth=False) == (200, {"status": "ok"})
    assert call("GET", "/tasks", auth=False)[0] == 401


def test_task_lifecycle_versioning_and_audit(repo):
    code, task = call("POST", "/tasks", body={"title": "Implement task API"})
    assert code == 201
    task_id = task["taskId"]
    assert call("GET", "/tasks/" + task_id)[1]["version"] == 1
    code, updated = call("PATCH", "/tasks/" + task_id, body={"status": "DONE", "version": 1})
    assert code == 200 and updated["version"] == 2
    assert call("PATCH", "/tasks/" + task_id, body={"title": "Stale", "version": 1})[0] == 409
    assert call("DELETE", "/tasks/" + task_id, params={"version": "2"})[0] == 204
    assert call("GET", "/tasks/" + task_id)[0] == 404
    assert [e["action"] for e in call("GET", "/audit", role="admin")[1]["items"]] == [
        "CREATED", "UPDATED", "DELETED"
    ]


def test_tenant_and_owner_isolation(repo):
    _, task = call("POST", "/tasks", body={"title": "Private"})
    uri = "/tasks/" + task["taskId"]
    assert call("GET", uri, tenant="another")[0] == 404
    assert call("GET", uri, subject="bob")[0] == 404
    assert call("DELETE", uri, subject="bob", params={"version": "1"})[0] == 404
    assert call("GET", "/tasks", subject="bob")[1]["items"] == []
    assert call("GET", uri, role="admin")[0] == 200
    assert call("GET", "/audit", role="member")[0] == 403


def test_request_validation(repo):
    assert call("POST", "/tasks", body={"title": ""})[0] == 400
    assert call("POST", "/tasks", body={"title": "ok", "isAdmin": True})[0] == 400
    assert call("GET", "/tasks", params={"limit": "1000"})[0] == 400
    assert call("GET", "/tasks/invalid")[0] == 400
    assert call("GET", "/wrong")[0] == 404
