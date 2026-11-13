"""DynamoDB single-table repository; atomic task mutations and audit events.

Tenant isolation is based on signed JWT claims, never a request header. Every
mutation is a DynamoDB transaction containing both task change and audit write.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.exceptions import ClientError

from .domain import ApiError, Identity, decode_cursor, encode_cursor


class DynamoRepository:
    def __init__(self, client=None, table=None):
        self.client = client or boto3.client("dynamodb")
        self.table = table or os.environ["TASKS_TABLE"]
        self.ser, self.de = TypeSerializer(), TypeDeserializer()

    def _s(self, value):
        return self.ser.serialize(value)

    def _encode(self, obj):
        return {k: self._s(v) for k, v in obj.items()}

    def _decode(self, obj):
        result = {k: self.de.deserialize(v) for k, v in obj.items()}
        return {k: (int(v) if isinstance(v, Decimal) and v % 1 == 0 else v) for k, v in result.items()}

    def _key(self, identity: Identity, task_id: str):
        return self._encode({"pk": identity.tenant_key, "sk": f"TASK#{task_id}"})

    def _audit(self, identity: Identity, task_id: str, action: str, at: str):
        return {"pk": identity.tenant_key, "sk": f"EVENT#{at}#{uuid.uuid4()}",
                "taskId": task_id, "actorId": identity.subject, "action": action, "createdAt": at}

    def _transaction(self, writes):
        try:
            self.client.transact_write_items(TransactItems=writes)
        except ClientError as exc:
            reasons = exc.response.get("CancellationReasons", [])
            if any(reason.get("Code") == "ConditionalCheckFailed" for reason in reasons):
                raise ApiError(409, "conflict", "Task changed; refresh and retry") from exc
            raise

    def create(self, identity: Identity, props: dict):
        task_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        task = {"pk": identity.tenant_key, "sk": f"TASK#{task_id}", "ownerPk": identity.owner_key,
                "taskId": task_id, "ownerId": identity.subject, "title": props["title"],
                "description": props.get("description", ""), "status": props.get("status", "OPEN"),
                "version": 1, "createdAt": now, "updatedAt": now}
        self._transaction([
            {"Put": {"TableName": self.table, "Item": self._encode(task),
                     "ConditionExpression": "attribute_not_exists(pk)"}},
            {"Put": {"TableName": self.table, "Item": self._encode(self._audit(identity, task_id, "CREATED", now))}},
        ])
        return task

    def get(self, identity: Identity, task_id: str):
        result = self.client.get_item(TableName=self.table, Key=self._key(identity, task_id), ConsistentRead=True)
        if "Item" not in result:
            raise ApiError(404, "not_found", "Task not found")
        task = self._decode(result["Item"])
        if not identity.admin and task["ownerId"] != identity.subject:
            raise ApiError(404, "not_found", "Task not found")
        return task

    def list_tasks(self, identity: Identity, limit: int, cursor: str | None):
        scope = identity.tenant_key + ("#ALL" if identity.admin else f"#USER#{identity.subject}")
        query = {"TableName": self.table, "Limit": limit,
                 "KeyConditionExpression": "pk = :p AND begins_with(sk, :s)" if identity.admin
                 else "ownerPk = :p AND begins_with(sk, :s)",
                 "ExpressionAttributeValues": {
                     ":p": self._s(identity.tenant_key if identity.admin else identity.owner_key),
                     ":s": self._s("TASK#")}}
        if not identity.admin:
            query["IndexName"] = "OwnerIndex"
        start = decode_cursor(cursor, scope)
        if start:
            query["ExclusiveStartKey"] = start
        result = self.client.query(**query)
        return {"items": [self._decode(item) for item in result.get("Items", [])],
                "nextCursor": encode_cursor(result.get("LastEvaluatedKey"), scope)}

    def update(self, identity: Identity, task_id: str, expected: int, props: dict):
        self.get(identity, task_id)
        now = datetime.now(timezone.utc).isoformat()
        props = {**props, "updatedAt": now}
        names = {"#ver": "version"}
        values = {":old": self._s(expected), ":new": self._s(expected + 1)}
        assignments = ["#ver = :new"]
        for i, (name, value) in enumerate(props.items()):
            names[f"#f{i}"] = name
            values[f":f{i}"] = self._s(value)
            assignments.append(f"#f{i} = :f{i}")
        self._transaction([
            {"Update": {"TableName": self.table, "Key": self._key(identity, task_id),
                        "UpdateExpression": "SET " + ", ".join(assignments),
                        "ConditionExpression": "attribute_exists(pk) AND #ver = :old",
                        "ExpressionAttributeNames": names, "ExpressionAttributeValues": values}},
            {"Put": {"TableName": self.table, "Item": self._encode(self._audit(identity, task_id, "UPDATED", now))}},
        ])
        return self.get(identity, task_id)

    def delete(self, identity: Identity, task_id: str, expected: int):
        self.get(identity, task_id)
        now = datetime.now(timezone.utc).isoformat()
        self._transaction([
            {"Delete": {"TableName": self.table, "Key": self._key(identity, task_id),
                        "ConditionExpression": "attribute_exists(pk) AND #ver = :old",
                        "ExpressionAttributeNames": {"#ver": "version"},
                        "ExpressionAttributeValues": {":old": self._s(expected)}}},
            {"Put": {"TableName": self.table, "Item": self._encode(self._audit(identity, task_id, "DELETED", now))}},
        ])

    def list_audit(self, identity: Identity, limit: int, cursor: str | None):
        scope = identity.tenant_key + "#AUDIT"
        query = {"TableName": self.table, "Limit": limit,
                 "KeyConditionExpression": "pk = :p AND begins_with(sk, :s)",
                 "ExpressionAttributeValues": {":p": self._s(identity.tenant_key), ":s": self._s("EVENT#")},
                 "ScanIndexForward": False}
        start = decode_cursor(cursor, scope)
        if start:
            query["ExclusiveStartKey"] = start
        result = self.client.query(**query)
        return {"items": [self._decode(item) for item in result.get("Items", [])],
                "nextCursor": encode_cursor(result.get("LastEvaluatedKey"), scope)}