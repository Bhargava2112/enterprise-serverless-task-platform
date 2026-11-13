"""Test low-level DynamoDB request shapes without external services."""
import pytest
from botocore.exceptions import ClientError

from taskplatform.domain import ApiError, Identity
from taskplatform.dynamo import DynamoRepository


class RecordingDynamo:
    def __init__(self):
        self.transactions = []
        self.queries = []
        self.saved = None
        self.fail = False

    def transact_write_items(self, **kwargs):
        if self.fail:
            raise ClientError({
                "Error": {"Code": "TransactionCanceledException", "Message": "Conflict"},
                "CancellationReasons": [{"Code": "ConditionalCheckFailed"}],
            }, "TransactWriteItems")
        self.transactions.append(kwargs["TransactItems"])
        if kwargs["TransactItems"][0].get("Put"):
            self.saved = kwargs["TransactItems"][0]["Put"]["Item"]

    def get_item(self, **kwargs):
        assert kwargs["ConsistentRead"] is True
        return {"Item": self.saved} if self.saved else {}

    def query(self, **kwargs):
        self.queries.append(kwargs)
        return {"Items": [self.saved] if self.saved else []}


def test_create_transaction_contains_task_and_audit():
    client = RecordingDynamo()
    store = DynamoRepository(client=client, table="example")
    alice = Identity("acme", "alice", "member")
    created = store.create(alice, {"title": "Cloud architecture"})
    writes = client.transactions[0]
    assert len(writes) == 2
    task, audit = writes[0]["Put"], writes[1]["Put"]
    assert task["TableName"] == audit["TableName"] == "example"
    assert task["ConditionExpression"] == "attribute_not_exists(pk)"
    assert task["Item"]["pk"]["S"] == "TENANT#acme"
    assert task["Item"]["ownerPk"]["S"] == "TENANT#acme#USER#alice"
    assert audit["Item"]["action"]["S"] == "CREATED"
    assert created["taskId"]


def test_owner_and_admin_query_access_patterns():
    client = RecordingDynamo()
    store = DynamoRepository(client=client, table="example")
    store.list_tasks(Identity("acme", "alice", "member"), 10, None)
    assert client.queries[-1]["IndexName"] == "OwnerIndex"
    assert client.queries[-1]["ExpressionAttributeValues"][":p"] == {"S": "TENANT#acme#USER#alice"}
    store.list_tasks(Identity("acme", "admin", "admin"), 10, None)
    assert "IndexName" not in client.queries[-1]
    assert client.queries[-1]["ExpressionAttributeValues"][":p"] == {"S": "TENANT#acme"}


def test_update_uses_version_condition_and_atomic_audit():
    client = RecordingDynamo()
    store = DynamoRepository(client=client, table="example")
    alice = Identity("acme", "alice", "member")
    task = store.create(alice, {"title": "before"})
    store.update(alice, task["taskId"], 1, {"title": "after"})
    writes = client.transactions[-1]
    assert len(writes) == 2
    update, event = writes[0]["Update"], writes[1]["Put"]
    assert update["ConditionExpression"] == "attribute_exists(pk) AND #ver = :old"
    assert update["ExpressionAttributeValues"][":old"] == {"N": "1"}
    assert event["Item"]["action"]["S"] == "UPDATED"


def test_transaction_conflicts_are_mapped_to_409():
    client = RecordingDynamo()
    client.fail = True
    store = DynamoRepository(client=client, table="example")
    with pytest.raises(ApiError) as raised:
        store.create(Identity("acme", "alice", "member"), {"title": "test"})
    assert raised.value.status == 409
