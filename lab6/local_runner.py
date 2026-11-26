"""Loopback HTTP adapter for the existing Lambda handler; no AWS deployment."""

import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import platform
import sys
from urllib.parse import urlsplit

if __package__:
    from .lambda_function import lambda_handler
else:
    from lambda_function import lambda_handler


MAX_BODY_BYTES = 1024 * 1024


class LambdaHTTPHandler(BaseHTTPRequestHandler):
    """Adapt HTTP framing to Gateway v2; route and validate JSON in Lambda."""

    timeout = 5
    server_version = "Lab6Local/1.0"
    sys_version = ""

    def __getattr__(self, name):
        # Every HTTP verb reaches Lambda, including unsupported/custom verbs.
        if name.startswith("do_"):
            return self._dispatch
        raise AttributeError(name)

    def _read_body(self):
        if self.headers.get("Transfer-Encoding") is not None:
            raise ValueError("Transfer-Encoding is unsupported; use Content-Length")
        lengths = self.headers.get_all("Content-Length", [])
        if len(lengths) > 1:
            raise ValueError("exactly one Content-Length header is allowed")
        length_text = lengths[0] if lengths else "0"
        if not length_text.isascii() or not length_text.isdecimal():
            raise ValueError("Content-Length must be a non-negative integer")
        length = int(length_text)
        if length > MAX_BODY_BYTES:
            raise ValueError("request body exceeds 1048576 bytes")
        body = self.rfile.read(length)
        if len(body) != length:
            raise ValueError("request body is shorter than Content-Length")
        return body

    def _dispatch(self):
        try:
            body_bytes = self._read_body()
            url = urlsplit(self.path)
        except (ValueError, TimeoutError) as error:
            self.send_error(400, str(error))
            return
        except OSError:
            self.close_connection = True
            return

        try:
            body = body_bytes.decode("utf-8")
            encoded = False
        except UnicodeDecodeError:
            # Gateway represents binary bodies as Base64; Lambda validates them.
            body = base64.b64encode(body_bytes).decode("ascii")
            encoded = True

        headers = {name.lower(): value for name, value in self.headers.items()}
        event = {
            "version": "2.0",
            "routeKey": "$default",
            "rawPath": url.path,
            "rawQueryString": url.query,
            "headers": headers,
            "requestContext": {"http": {
                "method": self.command,
                "path": url.path,
                "protocol": self.request_version,
                "sourceIp": self.client_address[0],
                "userAgent": headers.get("user-agent", ""),
            }},
            "body": body,
            "isBase64Encoded": encoded,
        }
        response = lambda_handler(event, None)
        self._write_response(response["statusCode"], response["headers"], response["body"])

    def _write_response(self, status, headers, body):
        payload = body.encode("utf-8")
        self.close_connection = True
        try:
            self.send_response(status)
            for name, value in headers.items():
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Connection", "close")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(payload)
        except OSError:
            # A disconnected client must not produce an unhandled traceback.
            pass

    def send_error(self, code, message=None, explain=None):
        # Keep transport/parser errors JSON too; do not parse application JSON here.
        message = message or self.responses.get(code, ("HTTP error",))[0]
        self._write_response(code, {"Content-Type": "application/json"}, json.dumps({"error": message}))


def create_server(port=8000):
    """Bind loopback only; port 0 lets integration tests select a free port."""
    return ThreadingHTTPServer(("127.0.0.1", port), LambdaHTTPHandler)


def main():
    try:
        port = int(os.environ.get("LAB6_PORT", "8000"))
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        print("LAB6_PORT must be an integer from 1 to 65535", file=sys.stderr)
        return 2

    try:
        server = create_server(port)
    except OSError as error:
        print(f"Cannot listen on 127.0.0.1:{port}: {error}. Choose a free LAB6_PORT.", file=sys.stderr)
        return 1

    with server:
        print(f"Lab 6 local runner listening on http://127.0.0.1:{port} (Python {platform.python_version()})", flush=True)
        print("Press Ctrl+C to stop. Local HTTP emulation; no AWS deployment.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nLocal runner stopped.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
