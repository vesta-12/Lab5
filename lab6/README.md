# Laboratory Work 6 — A Serverless Function and CI/CD

Student: Sofiya Serbina. Group: ICT4401-ENG-1. Course: Distributed & Cloud Computing.

## Submission through GitHub

Parts A, B and C are complete. The submitted code is on `lab6-serverless-ci`;
no separate laboratory submission ZIP is needed. The required CI build artifact
is still `lambda-package`.

- [Two-page report](report.pdf)
- [Genuine screenshots and coverage index](screenshots/README.md)
- [Original CI runs and job evidence](logs/part_c_ci_evidence.md)
- [Final 25-point criteria audit](logs/final_submission_audit.md)
- [Latest ci.yml push runs and artifacts](https://github.com/vesta-12/Lab5/actions/workflows/ci.yml?query=branch%3Alab6-serverless-ci)

Architecture: HTTP request -> Local Runner -> API Gateway v2 event ->
`lambda_handler` -> JSON response. GitHub separately runs Python 3.12 tests ->
`package` -> `lambda-package`. No AWS deployment or AWS cold-start timing is claimed.

## Stage 1: Part A — Function and Tests

`lambda_function.lambda_handler(event, context)` is a stateless Python 3.12
function for HTTP API Gateway payload format 2.0. It reads the HTTP method from
`requestContext.http.method` and the path from `rawPath`. No Flask, AWS SDK,
database, disk storage or third-party runtime package is required.

The selected execution option is **B-2: Local Run without AWS**. Part A contains
the function and direct tests; Part B adds the local HTTP adapter below.
Part C adds the GitHub Actions test-and-package pipeline described below.

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
[screenshots/README.md](screenshots/README.md). The final report and CI evidence
are linked in the submission section above.

Verified on Python **3.12.16**, pytest **8.3.5**: **39 passed** (19 unchanged
Part A cases and 20 actual HTTP/TCP cases). All 10 live curl checks passed,
including B1–B4, malformed JSON, Unicode, query routing and an alternate
`LAB6_PORT`; both invalid-port and occupied-port startup guards behaved correctly.
The original [JUnit results](logs/part_b_pytest.xml),
[HTTP observations](logs/part_b_http_results.json) and
[server stdout/stderr](logs/part_b_local_runner.log) are retained.
The demonstration server was stopped with Ctrl+C after verification.
The user-provided 1.png, 2.png and 3.png cover all five required Part B subjects.
Their contents are indexed in screenshots/README.md; no synthetic images were substituted.


## Stage 3: Part C — GitHub Actions CI/CD

Workflow: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).
The file was renamed without configuration changes to match the assignment.
Historical runs below retain their original lab6-ci.yml path and URLs.
It runs on every Git push to `lab6-serverless-ci` or `main`, with optional
`workflow_dispatch`. The three required evidence runs below were all triggered
by actual pushes to the Lab 6 branch. No main-branch merge or push was made.

The `test` job checks out the repository, selects Python 3.12, installs
`lab6/requirements-dev.txt` and executes `python -m pytest lab6/tests -v`.
All 39 original cases run, including real loopback HTTP tests. A failing pytest
exit code fails the job; no continue-on-error or failure masking is used.

The separate `package` job has `needs: test`. GitHub therefore skips it when
tests fail. After success it checks out the same commit and uses Python 3.12's
standard-library `zipfile` to build and verify `lambda_function.zip`. The ZIP
contains exactly **`lambda_function.py` at its root**, suitable for the handler
name `lambda_function.lambda_handler`. `actions/upload-artifact` publishes it
as **`lambda-package`** with a 90-day retention request.

| Push run | Commit | Actual tests | test | package | Artifacts | GitHub run |
| --- | --- | --- | --- | --- | --- | --- |
| 1 — GREEN | [8b6a176](https://github.com/vesta-12/Lab5/commit/8b6a176913980a6845d1fd6b67fa1de534e0cba2) | 39 passed | success | success | 1 | [Run 45892096178](https://github.com/vesta-12/Lab5/actions/runs/45892096178) |
| 2 — RED | [ebab758](https://github.com/vesta-12/Lab5/commit/ebab758d03f9fcbeb24080f4dbe1f5c928b680a6) | 39 passed, 1 intentional failure | failure | skipped | 0 | [Run 45892227649](https://github.com/vesta-12/Lab5/actions/runs/45892227649) |
| 3 — GREEN | [e96b2a3](https://github.com/vesta-12/Lab5/commit/e96b2a3e97b020593ce85cf5cc560e02cf6acaca) | 39 passed | success | success | 1 | [Run 45892413211](https://github.com/vesta-12/Lab5/actions/runs/45892413211) |

The RED commit adds only `tests/test_intentional_ci_failure.py`, whose explicit
false assertion demonstrates the required failure. Run 3 removes only that file.
The failed commit remains in history; the current test directory has no intentional
failure. Downloaded artifacts from both GREEN runs were checked for ZIP integrity,
root layout and exact equality with the handler source in their respective commits.
Local regression verification after Run 3 also passed **39/39 on Python 3.12.16**.

### Download the verified package

Open [the restored GREEN run](https://github.com/vesta-12/Lab5/actions/runs/45892413211), scroll to **Artifacts** and
select **lambda-package**. GitHub may require signing in to download it.
The artifact is [ID 15151678519](https://github.com/vesta-12/Lab5/actions/runs/45892413211/artifacts/15151678519); its API-reported expiry
is `2027-02-24T20:37:40Z`. The downloaded artifact bundle contains
`lambda_function.zip`; opening that inner archive reveals `lambda_function.py`.
The inner ZIP SHA-256 from the verified download is
`acdfac26e0eed72bd7d374e3a240e74a6077fe2320b24382f7f68ab105d0e2bf`.

Alternatively, after authenticating GitHub CLI:

```bash
gh run download 45892413211 --repo vesta-12/Lab5 \
  --name lambda-package --dir /tmp/lab6-ci-package
python3 -m zipfile -l /tmp/lab6-ci-package/lambda_function.zip
```

This workflow performs tests and package delivery only; it does not deploy to AWS.
B-2 needs no AWS account or access keys, so no AWS credentials or new repository
secrets were created. Workflow permissions are `contents: read`; checkout does
not persist credentials. Official Actions are pinned to exact commit SHAs.
GitHub supplies its own short-lived run credentials for normal checkout/artifact
operations; they are not source-code secrets.

Original API records, full job logs, artifact metadata and download checks are in
[logs/part_c_ci_evidence.md](logs/part_c_ci_evidence.md). Five genuine GitHub UI
captures and their provenance are indexed in
[screenshots/part_c_evidence.md](screenshots/part_c_evidence.md).

References: [GitHub job dependencies](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-jobs),
[official upload-artifact](https://github.com/actions/upload-artifact).
The final report is [report.pdf](report.pdf); submission is through GitHub,
without a separate laboratory submission ZIP.


## Demonstration for assessment

Open the repository root in PyCharm and select `lab6/.venv/bin/python` (Python
3.12). Use the setup instructions above for a fresh clone. In its terminal:

```bash
lab6/.venv/bin/python -m pytest lab6/tests -v
lab6/.venv/bin/python lab6/local_runner.py
```

The first command should show **39 passed**. Keep the second command running
and use another terminal:

```bash
curl -i http://127.0.0.1:8000/time
curl -i -H 'Content-Type: application/json' --data-binary '{"message":"Hello from Lab 6"}' http://127.0.0.1:8000/echo
curl -i -H 'Content-Type: application/json' --data-binary '{}' http://127.0.0.1:8000/echo
curl -i http://127.0.0.1:8000/unknown
```

Show **200 / 200 / 400 / 404** and the JSON bodies, then the server request log.
Stop only your demonstration server with Ctrl+C. Open the three historical CI
links in the table above to demonstrate GREEN / RED / GREEN without repeating
the intentional failure. On RED, show the skipped package job and zero artifacts;
on GREEN, download lambda-package and inspect the inner ZIP's root file.

Explain that the local runner only adapts HTTP to a Lambda event; tests protect
both contracts and packaging. B-2 emulates invocation locally and needs no AWS
keys. A real cold start is initialization overhead, not a measured result here.

To regenerate the report without running experiments:

```bash
lab6/.venv/bin/python -m pip install -r lab6/requirements-report.txt
lab6/.venv/bin/python lab6/scripts/build_report.py
```
