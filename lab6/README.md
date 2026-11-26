# Laboratory Work 6 — A Serverless Function and CI/CD

Student: Sofiya Serbina. Course: Distributed & Cloud Computing.

## Stage 1: Part A — Function and Tests

`lambda_function.lambda_handler(event, context)` is a stateless Python 3.12
function for HTTP API Gateway payload format 2.0. It reads the HTTP method from
`requestContext.http.method` and the path from `rawPath`. No Flask, AWS SDK,
database, disk storage or third-party runtime package is required.

The selected execution option is **B-2: Local Run without AWS**. This stage
contains only the function and direct automated tests. The local HTTP runner
and CI/CD configuration belong to later stages.

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

## Run the tests

From the repository root, using a separate environment:

```bash
python3.12 -m venv lab6/.venv
lab6/.venv/bin/python -m pip install -r lab6/requirements-dev.txt
lab6/.venv/bin/python -m pytest lab6/tests -v
```

If Python 3.12 is unavailable, an existing `uv` installation can provide an
isolated interpreter without replacing the system Python:

```bash
uv venv --python 3.12 lab6/.venv
uv pip install --python lab6/.venv/bin/python -r lab6/requirements-dev.txt
lab6/.venv/bin/python -m pytest lab6/tests -v
```

The ten test functions cover the endpoints, current timestamps, old response
fields and JSON value types, missing input, malformed/non-object JSON, method
routing, Unicode, empty strings and Base64 bodies. Parametrization exercises
19 input cases. All tests invoke the handler directly; no running server,
AWS account, credentials, Docker or network service is needed.
