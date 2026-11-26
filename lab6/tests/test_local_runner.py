"""Real HTTP/TCP integration tests of the local adapter on an ephemeral port."""

from datetime import datetime, timezone
from http.client import HTTPConnection, HTTPResponse
import json
import socket
from threading import Thread

import pytest

from lab6.local_runner import create_server


@pytest.fixture(scope="module")
def server_address():
    with create_server(0) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield server.server_address
        finally:
            server.shutdown()
            thread.join(timeout=5)
            assert not thread.is_alive()


def _request(address, method, path, body=None):
    connection = HTTPConnection(*address, timeout=10)
    try:
        connection.request(method, path, body=body, headers={"Content-Type": "application/json"})
        response = connection.getresponse()
        content_type = response.getheader("Content-Type")
        payload = response.read()
        assert content_type == "application/json"
        return response.status, json.loads(payload)
    finally:
        connection.close()


@pytest.mark.parametrize("path", ["/time", "/time?from=local&ignored=1"])
def test_http_time_and_query_string(server_address, path):
    before = datetime.now(timezone.utc)
    status, payload = _request(server_address, "GET", path)
    assert status == 200
    assert before <= datetime.fromisoformat(payload["time"]) <= datetime.now(timezone.utc)
    assert payload["server_time"] == payload["time"]
    assert payload["served_by"]


def test_http_echo_unicode_and_query_string(server_address):
    message = "Hello, Привет, 世界 👋"
    body = json.dumps({"message": message}, ensure_ascii=False).encode("utf-8")
    status, payload = _request(server_address, "POST", "/echo?ignored=1", body)
    assert status == 200
    assert payload["reply"] == payload["message"] == message


@pytest.mark.parametrize("body", [None, b"{}", b'{"message":', b"[]", b'{"message":"\xff"}'])
def test_http_invalid_payload_returns_json_400(server_address, body):
    status, payload = _request(server_address, "POST", "/echo", body)
    assert status == 400
    assert payload["error"]


@pytest.mark.parametrize("method,path", [
    ("GET", "/unknown"), ("GET", "/echo"), ("POST", "/time"),
    ("PUT", "/echo"), ("BREW", "/time"),
])
def test_http_unknown_method_or_path_returns_json_404(server_address, method, path):
    status, payload = _request(server_address, method, path)
    assert status == 404
    assert payload["error"] == "route not found"


def test_http_head_returns_status_without_response_body(server_address):
    connection = HTTPConnection(*server_address, timeout=10)
    try:
        connection.request("HEAD", "/time")
        response = connection.getresponse()
        assert response.status == 404
        assert response.getheader("Content-Type") == "application/json"
        assert response.read() == b""
    finally:
        connection.close()


@pytest.mark.parametrize("framing", [
    b"Content-Length: -1\r\n\r\n",
    b"Content-Length: invalid\r\n\r\n",
    b"Content-Length: 2\r\nContent-Length: 2\r\n\r\n{}",
    b"Content-Length: 1048577\r\n\r\n",
    b"Transfer-Encoding: chunked\r\n\r\n0\r\n\r\n",
    b"Content-Length: 100\r\n\r\n{}",
])
def test_http_malformed_framing_returns_json_400(server_address, framing):
    with socket.create_connection(server_address, timeout=10) as connection:
        connection.sendall(b"POST /echo HTTP/1.1\r\nHost: localhost\r\n" + framing)
        connection.shutdown(socket.SHUT_WR)
        response = HTTPResponse(connection)
        response.begin()
        assert response.status == 400
        assert response.getheader("Content-Type") == "application/json"
        assert json.loads(response.read())["error"]
