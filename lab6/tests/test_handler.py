"""Direct handler tests: no HTTP server, AWS credentials or external services."""

import base64
from datetime import datetime, timezone
import json
import socket

import pytest

from lab6.lambda_function import lambda_handler


def _event(method="POST", path="/echo", body=None, encoded=False):
    return {
        "version": "2.0",
        "requestContext": {"http": {"method": method}},
        "rawPath": path,
        "body": body,
        "isBase64Encoded": encoded,
    }


def _invoke(event, expected_status):
    response = lambda_handler(event, None)
    assert response["statusCode"] == expected_status
    assert response["headers"]["Content-Type"] == "application/json"
    assert isinstance(response["body"], str)
    payload = json.loads(response["body"])
    assert isinstance(payload, dict)
    if expected_status >= 400:
        assert isinstance(payload["error"], str) and payload["error"]
    return payload


def test_time_returns_current_time_and_legacy_fields():
    before = datetime.now(timezone.utc)
    payload = _invoke(_event("GET", "/time"), 200)
    after = datetime.now(timezone.utc)
    assert before <= datetime.fromisoformat(payload["time"]) <= after
    assert payload["server_time"] == payload["time"]
    assert payload["served_by"] == socket.gethostname()


def test_echo_returns_reply_and_legacy_message():
    payload = _invoke(_event(body=json.dumps({"message": "hello", "extra": 1})), 200)
    assert payload["reply"] == payload["message"] == "hello"


@pytest.mark.parametrize("body", [None, "", "{}"], ids=["missing-body", "empty-body", "missing-message"])
def test_required_input_returns_400(body):
    _invoke(_event(body=body), 400)


@pytest.mark.parametrize(
    "body",
    ['{"message":', '{"message": NaN}', '{"message": 1e309}'],
    ids=["truncated-json", "non-json-number", "numeric-overflow"],
)
def test_malformed_json_returns_400(body):
    _invoke(_event(body=body), 400)


@pytest.mark.parametrize("body", ["[]", "null"], ids=["array", "null"])
def test_non_object_json_returns_400(body):
    _invoke(_event(body=body), 400)


def test_unknown_path_returns_404():
    _invoke(_event("GET", "/unknown"), 404)


@pytest.mark.parametrize("method,path", [("POST", "/time"), ("GET", "/echo")])
def test_unsupported_method_and_path_returns_404(method, path):
    _invoke(_event(method, path), 404)


@pytest.mark.parametrize("message", ["Hello, Привет, 世界 👋", ""], ids=["unicode", "empty-string"])
def test_echo_preserves_unicode_and_empty_string(message):
    payload = _invoke(_event(body=json.dumps({"message": message}, ensure_ascii=False)), 200)
    assert payload["reply"] == payload["message"] == message


@pytest.mark.parametrize("message", [None, {"nested": [1, True]}], ids=["null-value", "structured-value"])
def test_echo_preserves_legacy_json_value_types(message):
    payload = _invoke(_event(body=json.dumps({"message": message})), 200)
    assert payload["reply"] == payload["message"] == message


@pytest.mark.parametrize("valid", [True, False], ids=["valid-base64", "invalid-base64"])
def test_gateway_base64_body(valid):
    body = base64.b64encode('{"message":"世界"}'.encode("utf-8")).decode("ascii") if valid else "%%%"
    payload = _invoke(_event(body=body, encoded=True), 200 if valid else 400)
    if valid:
        assert payload["reply"] == payload["message"] == "世界"
