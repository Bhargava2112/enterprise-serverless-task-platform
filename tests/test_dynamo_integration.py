"""DynamoDB integration-style tests running against the Moto AWS emulator."""
import os

import boto3
import pytest

moto = pytest.importorskip("moto")
from moto import mock_aws  # noqa: E402
from taskplatform.domain import ApiError, Identity  # noqa: E402
from taskplatform.dynamo import DynamoRepository  # noqa: E402


@pytest.fixture
def repository():
    with mock_aws():
        os.environ.update(AWS_DEFAULT_REGION="us-east-1", AWS_ACCESS_KEY_ID="testing",
                          AWS_SECRET_ACCESS_KEY="testing", TASKS_TABLE="tasks")
        client = boto3.client("dynamodb", region_name="us-east-1")
        client.create_table(
            TableName="tasks", BillingMode="PAY_PER_REQUEST",
            AttributeDefinitions=[{"AttributeName": k, "AttributeType": "S"} for k in ("pk", "sk", "ownerPk")],
            KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"},
                       {"AttributeName": "sk", "KeyType": "RANGE"}],
            GlobalSecondaryIndexes=[{"IndexName": "OwnerIndex", "KeySchema": [
                {"AttributeName": "ownerPk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"}],
                "Projection": {"ProjectionType": "ALL"}}],
        )
        yield DynamoRepository(client=client, table="tasks")


def test_atomic_mutations_and_audit(repository):
    alice = Identity("tenant-a", "alice", "member")
    admin = Identity("tenant-a", "admin", "admin")
    task = repository.create(alice, {"title": "Build API"})
    updated = repository.update(alice, task["taskId"], 1, {"status": "DONE"})
    assert updated["version"] == 2
    assert updated["status"] == "DONE"
    with pytest.raises(ApiError) as err:
        repository.update(alice, task["taskId"], 1, {"title": "stale"})
    assert err.value.status == 409
    repository.delete(alice, task["taskId"], 2)
    audit = repository.list_audit(admin, 25, None)
    assert {e["action"] for e in audit["items"]} == {"CREATED", "UPDATED", "DELETED"}


def test_owner_gsi_and_paginated_tenant_queries(repository):
    alice = Identity("tenant-a", "alice", "member")
    bob = Identity("tenant-a", "bob", "member")
    other_tenant = Identity("tenant-b", "alice", "member")
    admin = Identity("tenant-a", "admin", "admin")
    for i in range(5):
        repository.create(alice, {"title": f"Task {i}"})
    repository.create(bob, {"title": "Bob's task"})
    repository.create(other_tenant, {"title": "Other tenant"})
    first = repository.list_tasks(alice, 2, None)
    second = repository.list_tasks(alice, 2, first["nextCursor"])
    assert len(first["items"]) == len(second["items"]) == 2
    assert {t["ownerId"] for t in first["items"] + second["items"]} == {"alice"}
    assert len(repository.list_tasks(admin, 25, None)["items"]) == 6
    with pytest.raises(ApiError):
        repository.list_tasks(bob, 2, first["nextCursor"])
