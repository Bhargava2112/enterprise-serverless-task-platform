"""Validation, typed identity, error semantics and tenant-scoped keys."""
from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from typing import Any

TENANT_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
MAX_BODY_BYTES = 16384
STATUSES = {"OPEN", "IN_PROGRESS", "DONE"}


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


@dataclass(frozen=True)
class Identity:
    tenant: str
    subject: str
    role: str

    @property
    def admin(self) -> bool:
        return self.role == "admin"

    @property
    def tenant_key(self) -> str:
        return f"TENANT#{self.tenant}"

    @property
    def owner_key(self) -> str:
        return f"{self.tenant_key}#USER#{self.subject}"


def identity_from_event(event: dict[str, Any]) -> Identity:
    """JWT signatures are validated by API Gateway, not by this handler.

    The Lambda MUST NOT be invokable by untrusted principals outside API Gateway.
    """
    claims = (event.get("requestContext") or {}).get("authorizer") or {}
    claims = (claims.get("jwt") or {}).get("claims") or {}
    tenant, subject, role = claims.get("custom:tenant_id"), claims.get("sub"), claims.get("custom:role", "member")
    if (not isinstance(tenant, str) or not TENANT_RE.fullmatch(tenant)
            or not isinstance(subject, str) or not subject or role not in ("member", "admin")):
        raise ApiError(401, "unauthorized", "Authenticated tenant identity required")
    return Identity(tenant, subject, role)


def json_body(event: dict[str, Any]) -> dict[str, Any]:
    if event.get("isBase64Encoded"):
        raise ApiError(400, "invalid_json", "Base64-encoded bodies are not supported")
    text = event.get("body") or "{}"
    if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_BODY_BYTES:
        raise ApiError(413, "body_too_large", "Request body must be under 16 KiB")
    try:
        data = json.loads(text)
    except (ValueError, TypeError) as exc:
        raise ApiError(400, "invalid_json", "Expected a JSON object") from exc
    if not isinstance(data, dict):
        raise ApiError(400, "invalid_json", "Expected a JSON object")
    return data


def fields(data: dict[str, Any], *, creation: bool) -> dict[str, str]:
    allowed = {"title", "description", "status"} | (set() if creation else {"version"})
    if set(data) - allowed:
        raise ApiError(400, "invalid_fields", "Unexpected task fields")
    if creation and "title" not in data:
        raise ApiError(400, "invalid_title", "title is required")
    result = {}
    if "title" in data:
        title = data["title"]
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 200:
            raise ApiError(400, "invalid_title", "title must contain 1 to 200 characters")
        result["title"] = title.strip()
    if "description" in data:
        desc = data["description"]
        if not isinstance(desc, str) or len(desc) > 4000:
            raise ApiError(400, "invalid_description", "description must be at most 4000 characters")
        result["description"] = desc
    if "status" in data:
        if not isinstance(data["status"], str) or data["status"] not in STATUSES:
            raise ApiError(400, "invalid_status", "status must be OPEN, IN_PROGRESS or DONE")
        result["status"] = data["status"]
    if not creation and not result:
        raise ApiError(400, "empty_update", "No editable fields supplied")
    return result


def version(value: Any) -> int:
    if type(value) is not int or not 1 <= value <= 2147483647:
        raise ApiError(400, "invalid_version", "positive integer version is required")
    return value


def page_limit(raw: Any) -> int:
    try:
        limit = int(raw if raw is not None else 25)
    except (ValueError, TypeError) as exc:
        raise ApiError(400, "invalid_limit", "limit must be an integer") from exc
    if not 1 <= limit <= 100:
        raise ApiError(400, "invalid_limit", "limit must be between 1 and 100")
    return limit


def encode_cursor(key: dict | None, scope: str) -> str | None:
    if key is None:
        return None
    payload = json.dumps({"scope": scope, "key": key}, separators=(",", ":"))
    return base64.urlsafe_b64encode(payload.encode()).decode()


def decode_cursor(value: str | None, scope: str) -> dict | None:
    if not value:
        return None
    try:
        if len(value) > 4096:
            raise ValueError("cursor too long")
        payload = json.loads(base64.b64decode(value, altchars=b"-_", validate=True))
        key = payload["key"]
        if (payload["scope"] != scope or not isinstance(key, dict)
                or not isinstance(key.get("pk"), dict) or not isinstance(key.get("sk"), dict)):
            raise ValueError("invalid scope or key")
        return key
    except (ValueError, TypeError, KeyError) as exc:
        raise ApiError(400, "invalid_cursor", "Invalid pagination cursor") from exc