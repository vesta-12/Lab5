# Lab 5 - Service Requirements Specification (Version 4)

**Course:** Distributed & Cloud Computing  
**Laboratory:** NoSQL, Fault Tolerance and Load Balancing  
**Student:** Sofiya Serbina  
**Version:** 4.0 (evolved from Laboratories 2, 3 and 4)

## Version 4 scope and precedence

Lab 5 deploys only `/time`, `/echo` and the new `/records` API behind nginx, with MongoDB external to three stateless API instances. Lab 4's `/files` and `/counter`, its R13-R31 requirements and their evidence are preserved as historical requirements in the unchanged `lab4/` deployment. They are not asserted to be endpoints of the Lab 5 image. R1-R3 remain applicable and are re-tested. Section 11 below adds R32-R50 without renumbering any prior requirement. The inherited paths in Sections 1-10 refer to their original laboratories; current Lab 5 traceability is in Section 11.

## Version 3 scope and precedence (historical)

Sections 1-6 below preserve the Version 2 requirements and their historical deployment context. They continue to describe Lab 2 and Lab 3; their ports, Python 3.12 image, and statements that persistence is out of scope apply to those laboratories only. Lab 4 adds the requirements in Sections 7-10, runs locally on Python 3.9.6 at `127.0.0.1:5002`, and adds shared persistent storage. Lab 3 source files and deployment manifests remain unchanged. The `/time` and `/echo` response contracts are retained. Authentication and public deployment remain out of scope.

The previous specification had no R-numbered requirements (verified before editing). Section 7 assigns identifiers to the retained requirements before continuing with the new requirements.

## 1. Overview (retained Version 2 context)

Laboratory Work 2 implemented two communication approaches:

1. A synchronous REST API with `/time` and `/echo` endpoints.
2. An asynchronous message queue with a separate REST-based broker, producer, and consumer.

Laboratory Work 3 reuses the existing Flask REST API and deploys it as a Docker container, then as multiple Kubernetes pods. The API remains stateless, so separate instances can process requests independently. The `/time` response now identifies the container or pod that handled the request using the `served_by` field.

Only the REST API is included in the Docker image and Kubernetes deployment. The queue components from Lab 2 are **not deployed or tested** in this laboratory.

## 2. REST API (Version 2)

The API uses HTTP and returns JSON responses. Inside the container, Flask listens on `0.0.0.0:5000`. On the macOS host, Docker maps port `5001` to container port `5000`.

### GET /time

- **Method:** `GET`
- **Docker host URL:** `http://127.0.0.1:5001/time`
- **Kubernetes URL:** `<URL returned by minikube service my-api --url>/time`
- **Request body:** none
- **Success status:** `200 OK`

Example response:

```json
{
  "server_time": "2026-10-25 15:06:53.053678",
  "served_by": "6e7f69cd8125"
}
```

Response fields:

- `server_time` — the current server date and time, represented as a string.
- `served_by` — the hostname of the responding instance, obtained using Python's `socket.gethostname()`. It identifies a Docker container when run with Docker and a pod when run with Kubernetes.

The `served_by` field makes it possible to count responses from different pods and demonstrate request distribution through a Kubernetes Service.

### POST /echo

- **Method:** `POST`
- **Docker host URL:** `http://127.0.0.1:5001/echo`
- **Kubernetes URL:** `<URL returned by minikube service my-api --url>/echo`
- **Content-Type:** `application/json`

Example request:

```json
{
  "message": "hello"
}
```

**Success status:** `200 OK`

```json
{
  "message": "hello"
}
```

If the JSON body is missing or the `message` field is absent, the API returns **`400 Bad Request`**:

```json
{
  "error": "field 'message' is required"
}
```

The endpoint does not save requests or responses between calls.

## 3. Containerization and Deployment Requirements

### Docker

- The application code is stored in `app/app.py`.
- `app/requirements.txt` contains `flask`.
- The Dockerfile uses `python:3.12-slim` as its base image.
- The Dockerfile copies and installs dependencies before copying the application code, allowing Docker to reuse cached dependency layers.
- The image is built as `my-api:lab3`.
- Flask listens on `0.0.0.0` and container port `5000`.
- The Docker Compose service is named `api`, builds from `./app`, and maps host port `5001` to container port `5000`.

### Kubernetes

- A Deployment named `my-api` manages **3 replicas** under normal operation.
- All pods use the image `my-api:lab3`, loaded into Minikube.
- The pod labels and Deployment selector use `app: my-api`.
- A Service named `my-api`, of type `NodePort`, uses selector `app: my-api` and forwards Service port `80` to container port `5000`.
- The Service provides access to the pod replicas through one logical endpoint.
- Across **30 requests** to `/time`, the `served_by` field must identify at least **2 different pods**.
- If a pod is deleted, the Deployment should create a replacement to maintain the desired replica count.
- The API should remain accessible through the Service during pod replacement while other healthy replicas are available.
- Scaling to **5 replicas** and back to **3 replicas** must be demonstrated.

## 4. Constraints

- Protocol: HTTP; response format: JSON.
- Runtime: Python 3.12 and Flask in the container.
- The Docker container port is `5000`; the macOS host uses port `5001` because host port `5000` was previously occupied.
- The locally exposed Minikube Service URL and port are provided by `minikube service my-api --url` and may vary between runs.
- The API must not depend on local in-memory session state or on a particular pod to handle consecutive requests.
- Only the API is included in the container; the Lab 2 queue broker, producer, and consumer are out of scope.
- AWS resources, AWS credentials, and other secrets are not required and must not be included in the Docker image.
- Authentication, authorization, HTTPS, and persistent storage are outside the scope of this laboratory.

## 5. Assumptions

1. Docker Desktop, Minikube, and kubectl are installed and running on the local macOS machine.
2. The Docker image is available to the Minikube cluster before the Kubernetes Deployment starts.
3. Clients send correctly formatted JSON for successful `/echo` requests.
4. Each API replica can answer `/time` and `/echo` without shared application state.
5. The Kubernetes Service selects the API pods using matching labels.
6. Healthy replicas are available to handle requests while a deleted pod is being replaced.
7. The laboratory uses a small local workload for request distribution, self-healing, and scaling tests.

## 6. Lab 2 Message Queue (Previous Version - Not Deployed in Lab 3)

The earlier project also included a separate in-memory message queue broker on port `6000`, with one producer and one consumer. The queue functionality is retained as background information only and is **not part of the Lab 3 REST API container**.

### POST /queue/<topic>

Adds a message to a queue identified by its topic. Example: `POST http://127.0.0.1:6000/queue/orders`. A successful request returns `201 Created` with the queue status and topic.

### GET /queue/<topic>

Retrieves and removes the oldest message from the selected queue using FIFO order. It returns `200 OK` with the message if one exists, or `204 No Content` if the queue is empty.

In Lab 2, the producer sent approximately one message per second and the consumer took approximately three seconds to process a message. The broker stored messages only in memory, so restarting it could cause queued messages to be lost. These behaviors are not evaluated in Lab 3.

## 7. Requirement identifiers and verification traceability

The identifiers are stable starting with Version 3. A retained requirement is not claimed as re-executed unless explicitly stated. Container and Kubernetes tests remain Lab 3 evidence.

| ID | Requirement | Verification / evidence |
| --- | --- | --- |
| R1 | GET `/time` returns 200 with string `server_time` and `served_by`. | `tests/test_api.py::test_TC01_time_served_by_R1_R42`; [Lab 5 HTTP observations](logs/functional-http.jsonl) |
| R2 | POST `/echo` returns 200 and the submitted `message`. | `tests/test_api.py::test_TC02_echo_legacy_R2_R3`; [Lab 5 HTTP observations](logs/functional-http.jsonl) |
| R3 | Missing message or malformed/non-object JSON on `/echo` returns JSON 400. | `tests/test_api.py::test_TC02_echo_legacy_R2_R3`; live missing-message check |
| R4 | The REST process keeps no per-client session or file state on disk. | Code review of `app/app.py`; restart persistence check |
| R5 | Retain the Lab 3 Python 3.12 image and dependency-first Docker build. | Historical `app/Dockerfile`, unchanged; not re-run in Lab 4 |
| R6 | Retain Lab 3 container 5000 / host 5001 mapping. | Historical root Compose, unchanged; not re-run in Lab 4 |
| R7 | Retain the three-pod Deployment and matching NodePort Service. | Historical `k8s/`, unchanged; not re-run in Lab 4 |
| R8 | At least two pods serve the 30-request distribution test. | Historical Lab 3 evidence; not re-run in Lab 4 |
| R9 | Deployment replaces deleted pods while remaining pods serve requests. | Historical Lab 3 evidence; not re-run in Lab 4 |
| R10 | Demonstrate scaling 3 to 5 to 3 pods. | Historical Lab 3 evidence; not re-run in Lab 4 |
| R11 | Retain Lab 2 FIFO queue POST 201 / GET 200 or 204 behavior. | Historical broker, unchanged; outside Lab 4 execution scope |
| R12 | Do not embed AWS or RustFS credentials in code, images, or submission. | `.gitignore`; ZIP content and secret audit |
| R13 | POST `/files` stores a UTF-8 text object and returns unique UUID `file_id`, 201, and Location. | `test_upload_and_read`; `logs/api-storage.log` |
| R14 | GET `/files/<file_id>` returns exactly the original text and ID, 200; missing key returns JSON 404. | `test_upload_and_read`, `test_missing_and_invalid_file`; live log |
| R15 | File IDs must be lowercase UUID-shaped strings; invalid IDs return JSON 400 before storage access. | `test_missing_and_invalid_file`; live invalid-ID request |
| R16 | File upload requires a JSON object with non-empty string `text`; malformed JSON, invalid Unicode and wrong types return JSON 400. | `test_invalid_file_json`, `test_malformed_json`, `test_utf8_byte_limit`; live validation |
| R17 | Maximum decoded text is 65,536 UTF-8 bytes inclusive; larger text returns 400. Requests above 512 KiB also return JSON 400. | `test_utf8_byte_limit`; live over-limit checks; `logs/additional-live-checks.log` exact ASCII/Unicode limits and request limit |
| R18 | Use boto3, S3 signature v4 and path-style addressing with RustFS. Create `lab4-files` if absent; handle concurrent creation; permission errors return 503. | `test_bucket_creation_and_race`, `test_bucket_permission_not_hidden`; live S3 HEAD/LIST |
| R19 | Store objects only in RustFS, backed by `lab4_s3-data`. Objects survive Flask restart and RustFS force recreation without volume deletion. | `logs/api-storage.log`: both persistence assertions |
| R20 | S3 connection, timeout, credentials, permission and other service errors return JSON 503 without exposing secrets. | `test_storage_outage`; live stopped-RustFS POST and GET 503 |
| R21 | POST `/counter/increment` executes exactly one Redis INCR on configured primary, returns JSON integer `value`, `source: primary`, 200. | `test_counter_routing`; live E1-E4 |
| R22 | GET `/counter` reads Redis GET from requested source; absent key means 0; default source is primary; invalid/empty/repeated `from` returns JSON 400. | `test_counter_routing`, `test_counter_invalid_source`; live validation |
| R23 | Redis host/port and key are environment configuration; redirect writes by restarting with `REDIS_PRIMARY_PORT=6380`, without code edits. | `test_environment_ports`; `logs/E4-manual-failover.log` |
| R24 | Redis errors, timeouts, read-only primary and invalid stored integer return JSON 503; no automatic write retry or fallback. | `test_redis_outages`, `test_redis_readonly_and_bad_integer`; live E4 primary failure and `logs/additional-live-checks.log` replica failure |
| R25 | Run 100 sequential INCR / primary GET / replica GET iterations and count stale reads. No WAIT is used in the experiment. | `logs/E1-normal.log` contains all 100 iterations |
| R26 | Detach replica, perform 10 API increments, compare values, restore and measure convergence. | `logs/E2-replica-behind.log` |
| R27 | Demonstrate reading own write on primary versus stale detached replica after three writes. | `logs/E3-read-own-write.log` |
| R28 | Stop primary, read replica, observe write 503, promote, redirect, write, restart old primary and record both roles and divergent values. | `logs/E4-manual-failover.log` |
| R29 | After experiments restore one master and one linked replica while preserving the promoted node's newest counter value. Never remove S3 volume. | E4 restoration commands and final replication INFO |
| R30 | Configuration is loaded from environment or `lab4/.env`, relative to `app.py`; explicit environment values override `.env`. Direct launch respects `FLASK_PORT` (default 5002). | Startup provenance log; `test_environment_ports`; E4 restarts |
| R31 | Distinguish isolated mock tests from live infrastructure evidence; retain timestamped raw experiment logs and measured results. | `logs/unit-tests.log`, `logs/results.json`, E1-E4 logs |

## 8. Lab 4 API contract

Base URL: `http://127.0.0.1:5002`. All documented responses are JSON with `Content-Type: application/json`. This is a local educational service. Unknown routes and unsupported methods use Flask's standard 404/405 handling; the JSON error contract concerns the routes below. JSON object fields beyond the required fields are ignored.

| Method and route | Input | Successful response | Error statuses |
| --- | --- | --- | --- |
| GET `/time` | None | 200 `{"server_time":"...","served_by":"..."}` | - |
| POST `/echo` | `{"message":"hello"}`; `message` may have any JSON value, as in Lab 3 | 200 `{"message":"hello"}` | 400 missing field or invalid JSON object |
| POST `/files` | `{"text":"Hello from Lab 4"}`; application/json | 201 `{"file_id":"<lowercase UUID>"}`; `Location: /files/<file_id>` | 400 invalid/oversized input; 503 storage error |
| GET `/files/<file_id>` | Lowercase UUID-shaped ID | 200 `{"file_id":"<id>","text":"Hello from Lab 4"}` | 400 invalid ID; 404 absent object key; 503 storage/bucket or decoding error |
| POST `/counter/increment` | No body required; body is ignored | 200 `{"value":1,"source":"primary"}` | 503 primary unavailable or write fails |
| GET `/counter?from=primary` | `from` absent or exactly `primary` | 200 `{"value":1,"source":"primary"}` | 400 invalid/repeated source; 503 Redis error |
| GET `/counter?from=replica` | Exactly `from=replica` | 200 `{"value":1,"source":"replica"}` | 400 invalid/repeated source; 503 Redis error |

Errors have `{"error":"<human-readable message>"}`. Examples: `{"error":"file not found"}` (404), `{"error":"object storage unavailable"}` (503), `{"error":"redis primary unavailable"}` (503). File payloads are decoded to UTF-8 in memory and streamed to/from S3 without writing user files to the Flask disk. An externally inserted oversized or invalid-UTF-8 object produces 503. A missing bucket or denied access is a storage failure, not a claim that a file key is absent.

## 9. Consistency and failure assumptions

Redis replication is asynchronous. A successful INCR acknowledges execution on the configured primary, not durable acknowledgement by every replica. Reading from the primary after the write provides read-your-writes in these sequential tests while that primary remains authoritative. A replica may return a stale value, including while disconnected. `source` labels the configured client connection; it is not a dynamic Redis ROLE lookup. During E4, both configured clients may temporarily point to the promoted node.

Compose starts `redis-primary` as master at host 6379 and `redis-replica` as its slave at host 6380. Both use Redis 7, AOF, and separate persistent volumes. The API never promotes nodes, redirects itself or writes to the replica client. A stopped primary causes writes to return 503. Recovery requires an operator to promote the replica and restart the API with the new endpoint. Restarting the old primary can produce two masters; Redis does not merge their independent writes. Fence writers before reconciling. The experiment copies the promoted node to the old primary as a replica before returning to the default topology. Runtime REPLICAOF changes do not replace Compose startup configuration.

The Flask development server is bound to loopback with debug/reloader disabled. This deployment is for laboratory use. Redis and S3 ports are bound to loopback. No production high-availability, quorum or zero-data-loss guarantee is asserted.

## 10. Environment and reproduction

| Variable | Default / required meaning |
| --- | --- |
| `FLASK_PORT` | `5002` for `python app.py`; Flask CLI uses `--port` or `FLASK_RUN_PORT` instead |
| `RUSTFS_ACCESS_KEY`, `RUSTFS_SECRET_KEY` | Required local educational credentials; used by Compose and boto3; no default in source |
| `S3_ENDPOINT_URL` | `http://127.0.0.1:9000` |
| `S3_BUCKET` | `lab4-files` |
| `S3_REGION` | `us-east-1` signing region |
| `REDIS_PRIMARY_HOST`, `REDIS_PRIMARY_PORT` | `127.0.0.1`, `6379` |
| `REDIS_REPLICA_HOST`, `REDIS_REPLICA_PORT` | `127.0.0.1`, `6380` |
| `REDIS_COUNTER_KEY` | `lab4:counter`; database 0 |

The runner uses the standard topology and fixed host ports 5002/6379/6380 for reproducible E1-E4, while the API itself supports configurable Redis ports. See `README.md` for setup, isolated tests, full live experiments, log locations, screenshot provenance and safe restoration. Re-running the experiments increments existing data and replaces experiment logs; archive the previous evidence first.

## 11. Lab 5 requirements and traceability

| ID | Requirement | Test / current evidence |
| --- | --- | --- |
| R32 | MongoDB 7 runs as `rs0`, three named persistent members, one PRIMARY and two SECONDARY; initialization is idempotent and verifies existing configuration. | `run_suite.py`: topology and second init; `logs/replica-status.log` |
| R33 | POST `/records` stores a UUID-keyed text record and returns 201, `id`, `text`, `served_by`, Location; IDs are unique. | TC03, TC13; MongoDB inspection |
| R34 | GET `/records/<id>` returns stored text, id and serving hostname with 200; absent well-formed ID gives JSON 404. | TC04, TC05 |
| R35 | IDs must be lowercase UUID-shaped strings; malformed IDs return JSON 400 before MongoDB access. | TC06 |
| R36 | Uploads require application/json containing an object with a non-empty string `text`; malformed JSON, invalid Unicode, missing/wrong-type/empty text return JSON 400. Extra fields are ignored. | TC07, TC08, TC11 |
| R37 | A record has at most 65,536 decoded UTF-8 bytes (inclusive); larger text returns JSON 400. Flask rejects JSON bodies over 524,288 bytes with 400; nginx's outer transport limit is 2 MiB and may return its own 413 above it. | TC09, TC10, TC11 |
| R38 | PyMongo errors return JSON 503; MongoDB operations have a 4,000 ms client-side timeout, 3,000 ms server selection, 1,000 ms connect and 4,000 ms socket timeout. No uncaught traceback is exposed to clients. Full database outage checks must finish under the 12 s client timeout. | Controlled full outage; write/read probes |
| R39 | Insert uses `WriteConcern(w="majority", wtimeout=2500)` and retryable writes within the overall operation budget. Reads use PRIMARY preference and majority read concern. This is not an assertion of linearizable reads. | Source and runtime collection configuration; TC03; failover retention |
| R40 | Three API processes keep records only in MongoDB, with one shared MongoClient/pool per process. Data can be read through another API and after API restart. | TC12; restart/persistence and MongoDB inspection |
| R41 | Compose project is lab5. Only nginx is exposed on host loopback. MongoDB is on an internal Docker network, unexposed and unauthenticated for the local lab. Each node has its own named volume. URI and database are environment configuration. | Compose config, port and mount inspection |
| R42 | api1/api2/api3 run identical images on 0.0.0.0:5000, hostnames api1/api2/api3. GET `/time` retains R1; POST `/echo` retains R2/R3. | TC01, TC02, TC12; image inspection |
| R43 | Exactly 30 baseline GET `/time` requests via nginx must reach at least two API hostnames, with statuses and counts retained. | `distribution()` baseline; [logs/distribution-baseline.json](logs/distribution-baseline.json) |
| R44 | During a roughly 20 s api2 stop, only api1/api3 may answer the separate 30-request distribution. Probes quantify actual errors; api2 must rejoin after restart. nginx uses max_fails=1, fail_timeout=5s, bounded upstream attempts and no `non_idempotent` retry. | API failure scenario and probe_api_down.txt |
| R45 | Stopping the dynamically identified MongoDB primary triggers an automatic election; observe a different primary and successful writes while the old node is still stopped. No manual promotion/reconfiguration is allowed. | Primary failure scenario, role timeline and probe_primary_down.txt |
| R46 | Previously acknowledged control records remain readable after election and return of the old node. | Primary failure read probes and retention assertions |
| R47 | Run a fixed 3:1 GET /time:POST /records workload with 0.1-0.5 s think time at 10/50/100 users for 60 s each, preserving CSV, commands, ramp-up and resource samples. | [tests/locustfile.py](tests/locustfile.py); [scripts/run_suite.py](scripts/run_suite.py), functions `load_tests` / `load_level`; `logs/locust_*` |
| R48 | Self-selected educational targets, declared BEFORE measurements: aggregate and each endpoint p95 <= 1,000 ms and failure rate <= 1% at all three normal-load levels. RPS has no artificial minimum because think time limits offered load. These are not instructor-supplied SLAs. Optional saturation runs use the same workload and are exploratory. | Targets compared with original Locust stats CSV in test_report.md |
| R49 | At least eight traceable cases include negative, edge and failure cases; preserve actual/expected outcomes, per-request timings, fault command times, resources and unmodified CSV. | functional-results.jsonl, raw requests CSV, run summary, report |
| R50 | Every controlled stop restores Lab 5 services, verifies one primary/two secondaries and retains volumes and prior labs. Evidence is immutable; repeat runs have unique directories. | finally blocks, final topology, original-file audit |

These targets are versioned before running load. A failed target remains FAIL; the limits must not be relaxed after measurement to manufacture a pass.

## 12. Lab 5 API and timing contract

Public base URL defaults to `http://127.0.0.1:8080` through nginx. `LAB5_HTTP_PORT` changes only the host mapping; clients use matching `BASE_URL`. API processes always bind container port 5000. The Lab 4 host port 5002 is unrelated.

| Method and route | Request | Response |
| --- | --- | --- |
| GET `/time` | None | 200 `{"server_time":"...","served_by":"api1"}` |
| POST `/echo` | `{"message":"hello"}` | 200 `{"message":"hello"}`; missing field/non-object JSON: 400 |
| POST `/records` | `{"text":"Hello from Lab 5"}` | 201 `{"id":"<uuid>","text":"Hello from Lab 5","served_by":"api1"}` and relative Location |
| GET `/records/<id>` | UUID-shaped lowercase ID | 200 `{"id":"<uuid>","text":"Hello from Lab 5","served_by":"api2"}`; absent ID 404 |

All application errors use JSON `{"error":"..."}`. Invalid input is 400; MongoDB exceptions are 503 `{"error":"storage unavailable"}`. Route/method errors and nginx transport errors may use framework/proxy defaults. nginx forwards storage 503 rather than treating it as a failed application host.

MongoDB operations use a 4 s overall PyMongo budget. A failed pool acquisition/selection or write concern can finish earlier. nginx uses 1 s connect and 7 s send/read idle timeouts, at most 3 upstream tries and an 8 s upstream-retry budget; only safe/eligible retry conditions are enabled. Probes/integration HTTP requests use 12 s timeout. A successful response is an acknowledgement from the configured MongoDB concern; a timeout/503 can have an uncertain write outcome. The API makes no general exactly-once promise.

With client-side operation timeout enabled, PyMongo derives the effective write timeout from the remaining operation budget; the configured 2.5 s write-concern timeout is not an additional independent deadline. End-to-end HTTP timings also include scheduling and response overhead, so the 4 s driver budget is not an exact 4.000 s HTTP guarantee. The live outage assertion is below the 12 s HTTP-client limit.

The Gunicorn image has one process and four threads per API (three processes / twelve threads in total), no preloading, timeout 15 s, graceful timeout 5 s. MongoClient has maxPoolSize 40, waitQueueTimeoutMS 1000, retryWrites true. WiredTiger cache is explicitly 0.25 GiB per MongoDB node to fit alongside previous lab services on this local Docker VM. This is a local educational configuration, not a production capacity recommendation.

## 13. Failure and measurement semantics

The workload is unchanged between comparable load levels. CSV statistics include the documented spawn ramp; an explicit warm-up happens before each measured run. Original Locust histogram percentiles are retained; per-request raw CSV supports independent inspection. The controlled API and MongoDB failures occur outside the normal-load runs.

The sequential probe targets starts every 0.5 s only while responses are fast enough. It records both ends and elapsed time; a slow request lengthens the actual interval. Timeline durations use monotonic clocks. Recovery is the first observed successful response after an observed error interval, with requests that started before stop excluded from post-stop classification. If no error occurs, report no observed failed probe instead of inventing an outage. Election detection is sampled independently through surviving MongoDB members. Loss of one node leaves two voting members; after election the majority can resume writes.

The experiment is a node-stop test, not a direct network-partition proof of CAP. During a partition the chosen primary/majority policy prevents the minority from acknowledging majority writes. Reads from a secondary would trade freshness for read scaling and some read availability; this API deliberately uses primary/majority reads.

## 14. Current environment variables

| Variable | Meaning / default |
| --- | --- |
| `MONGO_URI` | Required in API containers; all mongo1/mongo2/mongo3 seeds with replicaSet=rs0 |
| `MONGO_DB` | `lab5` |
| `LAB5_HTTP_PORT` | Compose host port, default `8080` on 127.0.0.1 |
| `BASE_URL` | Test public base URL, default `http://127.0.0.1:8080` |
| `LAB5_RUN_DIR` | Unique evidence directory used by pytest |
| `LAB5_RAW_CSV` | Per-request Locust CSV path |
| `LAB5_RUN_ID` | Test-data/probe run identifier |

No credentials or AWS services are required. Normal pytest does not stop containers; full outages and election tests are explicit in `scripts/run_suite.py`. Historical sections remain unchanged except the specification's overall version/scope header.
