"""Stateless HTTP API Gateway v2 handler for Laboratory Work 6."""

import base64
import binascii
from datetime import datetime, timezone
import json
import math
import socket
from typing import Any


def _response(status: int, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload, allow_nan=False),
    }


def _reject_nonfinite(value: str) -> None:
    raise ValueError(f"{value} is not a JSON number")


def _finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("number exceeds the supported finite range")
    return number


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Return a proxy response without AWS clients, servers or persistent state."""
    request_context = event.get("requestContext")
    http = request_context.get("http") if isinstance(request_context, dict) else None
    method = http.get("method") if isinstance(http, dict) else None
    path = event.get("rawPath")

    if method == "GET" and path == "/time":
        timestamp = datetime.now(timezone.utc).isoformat()
        return _response(200, {
            "time": timestamp,
            "server_time": timestamp,
            "served_by": socket.gethostname(),
        })

    if method == "POST" and path == "/echo":
        body = event.get("body")
        try:
            if not isinstance(body, str):
                raise ValueError("body must be JSON text")
            if event.get("isBase64Encoded", False):
                body = base64.b64decode(body, validate=True).decode("utf-8")
            data = json.loads(body, parse_constant=_reject_nonfinite, parse_float=_finite_float)
        except (ValueError, UnicodeError, binascii.Error):
            return _response(400, {"error": "body must contain valid JSON"})

        if not isinstance(data, dict) or "message" not in data:
            return _response(400, {"error": "field 'message' is required"})

        # R2 permits any JSON value; do not narrow the inherited echo contract.
        return _response(200, {"reply": data["message"], "message": data["message"]})

    return _response(404, {"error": "route not found"})
