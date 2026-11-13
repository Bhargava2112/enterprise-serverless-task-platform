import base64
import json

import pytest

from taskplatform.domain import (
    ApiError,
    Identity,
    decode_cursor,
    encode_cursor,
    fields,
    identity_from_event,
    json_body,
    page_limit,
    version,
)


def claims(tenant="acme", subject="u1", role="member"):
    return {"requestContext": {"authorizer": {"jwt": {"claims": {
        "custom:tenant_id": tenant, "sub": subject, "custom:role": role
    }}}}}


def test_claims_are_required_and_strict():
    assert identity_from_event(claims()) == Identity("acme", "u1", "member")
    for event in [{}, claims("../../other"), claims(role="root"), claims(subject="")]:
        with pytest.raises(ApiError) as exc:
            identity_from_event(event)
        assert exc.value.status == 401


def test_member_and_admin_partition_keys():
    identity = Identity("acme", "alice", "member")
    assert identity.tenant_key == "TENANT#acme"
    assert identity.owner_key == "TENANT#acme#USER#alice"
    assert not identity.admin
    assert Identity("acme", "alice", "admin").admin


@pytest.mark.parametrize("bad", [{"title": ""}, {"title": "  "}, {"title": "a" * 201},
                                   {"title": 15}, {"title": "ok", "admin": True},
                                   {"title": "ok", "status": "ARCHIVED"}])
def test_invalid_create_body(bad):
    with pytest.raises(ApiError):
        fields(bad, creation=True)


def test_field_rules_and_update_allowlist():
    assert fields({"title": "  Design the API ", "status": "OPEN"}, creation=True) == {
        "title": "Design the API", "status": "OPEN"
    }
    assert fields({"version": 1, "status": "DONE"}, creation=False) == {"status": "DONE"}
    for data in [{}, {"version": 1}, {"title": 2}]:
        with pytest.raises(ApiError):
            fields(data, creation=False)


@pytest.mark.parametrize("bad", [True, False, 0, -1, 1.0, "1", None, 2147483648])
def test_version_rejects_bad_values(bad):
    with pytest.raises(ApiError):
        version(bad)


def test_json_body_enforces_object_and_size():
    assert json_body({"body": '{"title": "t"}'}) == {"title": "t"}
    for body in ["[]", "null", "{bad json", '"just a string"', "x" * 17000]:
        with pytest.raises(ApiError):
            json_body({"body": body})
    with pytest.raises(ApiError):
        json_body({"isBase64Encoded": True, "body": "e30="})


def test_limit_is_bounded():
    assert page_limit(None) == 25
    assert page_limit("100") == 100
    for value in ["0", "101", "abc", "-1", "100000"]:
        with pytest.raises(ApiError):
            page_limit(value)


def test_cursors_cannot_be_reused_across_principals():
    raw_key = {"pk": {"S": "TENANT#acme"}, "sk": {"S": "TASK#x"}}
    cursor = encode_cursor(raw_key, "TENANT#acme#USER#alice")
    assert decode_cursor(cursor, "TENANT#acme#USER#alice") == raw_key
    with pytest.raises(ApiError):
        decode_cursor(cursor, "TENANT#acme#USER#bob")
    with pytest.raises(ApiError):
        decode_cursor(base64.urlsafe_b64encode(json.dumps({"scope": "x", "key": []}).encode()).decode(), "x")
    with pytest.raises(ApiError):
        decode_cursor("????", "x")
