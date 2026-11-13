"""AWS Lambda handler for API Gateway HTTP API payload format 2.0."""
import json
import logging
import os
import uuid

from botocore.exceptions import ClientError

from .domain import ApiError, fields, identity_from_event, json_body, page_limit, version
from .dynamo import DynamoRepository

LOG = logging.getLogger(__name__)
LOG.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def response(status: int, payload: dict | None = None) -> dict:
    return {"statusCode": status, "headers": {"content-type": "application/json", "cache-control": "no-store",
                                              "x-content-type-options": "nosniff"},
            "body": "" if payload is None else json.dumps(payload, separators=(",", ":"))}


def lambda_handler(event: dict, _context=None) -> dict:
    request_context = event.get("requestContext") or {}
    request_id = request_context.get("requestId") or str(uuid.uuid4())
    http = request_context.get("http") or {}
    method = http.get("method")
    path = (event.get("rawPath") or "/").rstrip("/")
    # HTTP API stage mappings can add /v1; remove only a leading stage segment.
    if path.startswith("/v1/"):
        path = path[3:]
    try:
        if method == "GET" and path == "/health":
            return response(200, {"status": "ok"})
        identity = identity_from_event(event)
        store = DynamoRepository()
        params = event.get("queryStringParameters") or {}
        if path == "/tasks":
            if method == "POST":
                return response(201, store.create(identity, fields(json_body(event), creation=True)))
            if method == "GET":
                return response(200, store.list_tasks(identity, page_limit(params.get("limit")), params.get("cursor")))
        if path.startswith("/tasks/") and path.count("/") == 2:
            task_id = path.rsplit("/", 1)[-1]
            try:
                uuid.UUID(task_id)
            except (ValueError, AttributeError) as exc:
                raise ApiError(400, "invalid_task_id", "taskId must be a UUID") from exc
            if method == "GET":
                return response(200, store.get(identity, task_id))
            if method == "PATCH":
                body = json_body(event)
                return response(200, store.update(identity, task_id, version(body.get("version")), fields(body, creation=False)))
            if method == "DELETE":
                raw = params.get("version")
                try:
                    expected = int(raw)
                except (ValueError, TypeError) as exc:
                    raise ApiError(400, "invalid_version", "version query parameter is required") from exc
                store.delete(identity, task_id, version(expected))
                return response(204)
        if path == "/audit" and method == "GET":
            if not identity.admin:
                raise ApiError(403, "forbidden", "Admin role required")
            return response(200, store.list_audit(identity, page_limit(params.get("limit")), params.get("cursor")))
        return response(404, {"error": "not_found", "message": "Unknown route"})
    except ApiError as exc:
        return response(exc.status, {"error": exc.code, "message": exc.message})
    except ClientError:
        LOG.exception("AWS request failed request_id=%s", request_id)
        return response(503, {"error": "unavailable", "message": "Backend unavailable"})
    except Exception:
        LOG.exception("Unhandled error request_id=%s", request_id)
        return response(500, {"error": "internal_error", "message": "Internal server error"})