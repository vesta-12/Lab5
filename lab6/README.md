# Laboratory Work 6 — A Serverless Function and CI/CD

Student: Sofiya Serbina. Course: Distributed & Cloud Computing.

## Stage 1: Part A — Function and Tests

`lambda_function.lambda_handler(event, context)` is a stateless Python 3.12
function for HTTP API Gateway payload format 2.0. It reads the HTTP method from
`requestContext.http.method` and the path from `rawPath`. No Flask, AWS SDK,
database, disk storage or third-party runtime package is required.

The selected execution option is **B-2: Local Run without AWS**. Part A contains
the function and direct tests; Part B adds the local HTTP adapter below.
CI/CD configuration belongs to a later stage.

## API and compatibility

| Method and path | Input | Status and JSON response |
| --- | --- | --- |
| GET `/time` | No body required | 200: `{"time":"<UTC timestamp>","server_time":"<same timestamp>","served_by":"<runtime hostname>"}` |
| POST `/echo` | JSON object containing `message` | 200: `{"reply":<value>,"message":<same value>}` |
| POST `/echo` | Missing/empty body, malformed JSON, non-object JSON or absent `message` | 400: `{"error":"..."}` |
| Any other method/path combination | Any | 404: `{"error":"route not found"}` |

Every response has `statusCode`, `headers` and a JSON **string** in `body`.
`Content-Type` is `application/json`. Base64-encoded Gateway bodies are decoded
when `isBase64Encoded` is true; invalid Base64 or invalid UTF-8 produces 400.
Non-standard JSON constants such as `NaN` and `Infinity`, and numbers that
overflow Python's finite floating-point range, produce 400.

Lab 5 specification v4 requirements R1–R3 are preserved by adding aliases:
`time` equals the existing `server_time`, while `reply` equals the existing
`message`. The current timestamp is an ISO 8601 string with an explicit UTC
offset; `served_by` remains the runtime hostname. As in Lab 5, `message` may
contain **any JSON value**, including an empty string, Unicode, null or a nested
object. An absent field is different from a present field with a null value.
Extra request fields are ignored. Unknown routes and unsupported methods use
the Lab 6 JSON 404 contract. No previous laboratory code or specification is
modified.

## Run the Part A tests

From the repository root, using a separate environment:

```bash
python3.12 -m venv lab6/.venv
lab6/.venv/bin/python -m pip install -r lab6/requirements-dev.txt
lab6/.venv/bin/python -m pytest lab6/tests/test_handler.py -v
```

If Python 3.12 is unavailable, an existing `uv` installation can provide an
isolated interpreter without replacing the system Python:

```bash
uv venv --python 3.12 lab6/.venv
uv pip install --python lab6/.venv/bin/python -r lab6/requirements-dev.txt
lab6/.venv/bin/python -m pytest lab6/tests/test_handler.py -v
```

The ten test functions cover the endpoints, current timestamps, old response
fields and JSON value types, missing input, malformed/non-object JSON, method
routing, Unicode, empty strings and Base64 bodies. Parametrization exercises
19 input cases. These Part A tests invoke the handler directly; no running server,
AWS account, credentials, Docker or network service is needed.

## Stage 2: Part B — Local HTTP runner (B-2)

Use Python 3.12 and the separate `lab6/.venv` environment prepared above.
From the repository root:

```bash
lab6/.venv/bin/python lab6/local_runner.py
```

The server listens on **http://127.0.0.1:8000**. Keep that terminal running;
press **Ctrl+C** in the same terminal to stop it. To change the port:

```bash
LAB6_PORT=8001 lab6/.venv/bin/python lab6/local_runner.py
```

`LAB6_PORT` must be an integer from 1 to 65535. If a port is occupied, inspect
its listener with `lsof -nP -iTCP:8000 -sTCP:LISTEN` and choose a free port;
do not terminate an unrelated process. The server always binds loopback.
Running `lab6/.venv/bin/python -m lab6.local_runner` is also supported.

In PyCharm, open the repository root, select `lab6/.venv/bin/python` as the
interpreter and run `lab6/local_runner.py`. Alternatively, use the command
above in PyCharm's terminal. No packages beyond Python's standard library are
needed to run the server; pytest is only a development dependency.

### Demonstrate with curl

Run these in a second terminal. Adjust the port if `LAB6_PORT` was changed.

```bash
curl -i http://127.0.0.1:8000/time
curl -i -H 'Content-Type: application/json' \
  --data-binary '{"message":"Hello from Lab 6"}' http://127.0.0.1:8000/echo
curl -i -H 'Content-Type: application/json' \
  --data-binary '{}' http://127.0.0.1:8000/echo
curl -i -H 'Content-Type: application/json' \
  --data-binary '{"message":' http://127.0.0.1:8000/echo
curl -i http://127.0.0.1:8000/unknown
curl -i -H 'Content-Type: application/json' \
  --data-binary '{"message":"Hello, Привет, 世界 👋"}' http://127.0.0.1:8000/echo
curl -i 'http://127.0.0.1:8000/time?ignored=1'
```

Expected statuses are **200, 200, 400, 400, 404, 200, 200** in that order.
Both old and new response fields remain available. Unicode is preserved;
JSON escape sequences in curl output represent the same decoded characters.

### Adapter behavior

The adapter separates URL path from query string, reads exactly the declared
body length in bytes, and creates an HTTP API Gateway v2 event. `rawPath` is
the path, `rawQueryString` is the query, and `requestContext.http.method` is
the incoming method. Headers and client/protocol information are included.
UTF-8 bodies become text; binary bodies use Base64 with `isBase64Encoded`.

It calls the existing `lambda_handler(event, None)` once and forwards its
`statusCode`, headers and body. Application routing and JSON/message validation
remain in the unchanged handler. Response `Content-Length` uses the encoded
byte count. HEAD returns headers without a response body, as HTTP requires.

Transport guards return JSON 400 for invalid/duplicate/negative Content-Length,
bodies over 1 MiB, truncated bodies and body-read timeouts (5 seconds).
Chunked transfer encoding is deliberately unsupported and returns JSON 400;
the documented curl commands send Content-Length. Connections close after each
response. Disconnected clients are handled without an unhandled traceback.

This is **local HTTP emulation**, not an AWS deployment or a full API Gateway
emulator. It does not measure or claim AWS cold-start behavior.

### HTTP integration tests and evidence

```bash
# Part A: direct handler calls (19 cases)
lab6/.venv/bin/python -m pytest lab6/tests/test_handler.py -v
# Part B: real HTTP/TCP against a temporary local server
lab6/.venv/bin/python -m pytest lab6/tests/test_local_runner.py -v
# Both parts
lab6/.venv/bin/python -m pytest lab6/tests -v
```

HTTP tests bind an OS-selected free loopback port, so the demonstration server
can continue using 8000. Tests shut down only their own temporary server.
The suite covers time/query routing, Unicode echo, JSON errors, invalid UTF-8,
unsupported routes/methods, HEAD semantics and malformed HTTP body framing.

Original curl output is retained in [logs/part_b_http_checks.log](logs/part_b_http_checks.log).
Screenshot commands and capture status are documented in
[screenshots/README.md](screenshots/README.md). CI/CD, a final report and a ZIP
are intentionally outside this stage.

Verified on Python **3.12.16**, pytest **8.3.5**: **39 passed** (19 unchanged
Part A cases and 20 actual HTTP/TCP cases). All 10 live curl checks passed,
including B1–B4, malformed JSON, Unicode, query routing and an alternate
`LAB6_PORT`; both invalid-port and occupied-port startup guards behaved correctly.
The original [JUnit results](logs/part_b_pytest.xml),
[HTTP observations](logs/part_b_http_results.json) and
[server stdout/stderr](logs/part_b_local_runner.log) are retained.
The demonstration server was stopped with Ctrl+C after verification.
Five native terminal screenshots are pending manual capture as documented in
the screenshot checklist; no synthetic images have been substituted.
