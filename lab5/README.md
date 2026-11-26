# Laboratory Work 5 - NoSQL, Fault Tolerance and Load Balancing

Student: Sofiya Serbina. Course: Distributed & Cloud Computing. Group: ICT4401-ENG-1.

This laboratory lives in `lab5/` on `lab5-nosql-fault-tolerance`, based on the completed Lab 4 branch. Earlier laboratory code, deployments, reports and evidence stay unchanged. Current results are generated from the real evidence in `logs/`, never from mocked responses.

## Architecture

Only nginx is published, by default on `127.0.0.1:8080`. It balances requests between identical api1/api2/api3 instances. Each uses one Gunicorn worker with four threads, listens inside Docker on `0.0.0.0:5000` and reports its hostname in `/time` and record responses. MongoDB runs as rs0 with mongo1/mongo2/mongo3, one primary and two secondaries. Each node has a separate persistent volume. An idempotent one-shot mongo-init service verifies/initializes the set and waits for election before APIs start; its `Exited (0)` state is expected.

MongoDB ports and API ports are not published. MongoDB uses an internal backend network; APIs also join the nginx frontend network. This is an unauthenticated local educational cluster, not a public service. No AWS account or credentials are used. A 0.25 GiB WiredTiger cache per MongoDB node limits memory use alongside existing Lab 4 services. The actual host/VM resources and image versions are retained in `logs/environment.json`.

## Setup

```bash
cd /Users/sofiyaserbina/Lab3_Docker_Kubernetes_Lab4/lab5
git branch --show-current
# Expected: lab5-nosql-fault-tolerance
docker compose up -d --build
docker compose ps --all
docker compose exec mongo1 mongosh --quiet /scripts/init-replica.js
docker compose exec mongo1 mongosh --quiet --eval \
  "rs.status().members.map(m => m.name + ' ' + m.stateStr)"
docker compose exec nginx nginx -t
```

The repeat init command verifies the existing configuration and performs no forced reconfiguration. Compose explicitly uses project name lab5. Do not execute these commands from the repository root's older Compose file. Never remove the existing volumes with `down -v`.

For a standalone submission ZIP, change into its extracted `lab5/` directory instead of the original absolute path. Git and the old laboratories are not required to run the API/tests there. Branch protection is checked only when a real checkout is present; `scripts/run_suite.py --check-location` verifies this without starting tests. The final verifier explicitly marks the old-lab audit as not applicable in a standalone copy rather than claiming to have checked absent files.

If 8080 is occupied, inspect its owner and use a free port, for example `LAB5_HTTP_PORT=8081 docker compose up -d`; set `BASE_URL=http://127.0.0.1:8081` for all tests. Do not kill another listener. Container port 5000 is independent of macOS Control Center and Lab 4's host port 5002.

## API demonstration

```bash
curl -i http://127.0.0.1:8080/time
curl -i -H 'Content-Type: application/json' \
  -d '{"message":"hello"}' http://127.0.0.1:8080/echo
curl -i -H 'Content-Type: application/json' \
  -d '{"text":"Hello from Lab 5"}' http://127.0.0.1:8080/records
# Substitute the id returned by POST:
curl -i http://127.0.0.1:8080/records/<id>
curl -i http://127.0.0.1:8080/records/00000000-0000-4000-8000-000000000000
```

POST returns 201 after MongoDB acknowledges a majority write. GET returns 200 with the original record or 404 for an absent well-formed ID. Both include the API hostname; the serving instance can change. Invalid JSON/type/empty text/ID and text above 65,536 UTF-8 bytes produce 400. MongoDB failures produce JSON 503. `/time` does not query the database and can still return 200 while storage is down.

The API uses primary reads with majority read concern. It does not read from a local dictionary, cache user records or save them on container disk. PyMongo's overall operation timeout is 4 s; selection 3 s, connect 1 s, socket 4 s; write concern timeout 2.5 s. The client has one pool per process and bounded wait. nginx read/send timeout is 7 s with at most three eligible upstream tries; probes use 12 s HTTP timeouts. Retries of non-idempotent operations are not enabled in nginx, and MongoDB 503 is not hidden by proxy failover.

With PyMongo's client-side operation timeout active, its remaining budget governs the effective write timeout rather than a separate 2.5 s deadline. End-to-end HTTP time can exceed the nominal driver budget because of scheduling/response overhead; the suite verifies that controlled-outage responses arrive before the 12 s HTTP timeout.

## Functional tests

Use a separate environment; do not change Lab 4's environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-test.txt
.venv/bin/python -m pytest tests/test_api.py -v
```

The pinned test packages support the verified Python 3.9.6. These are real HTTP integration tests through nginx, without mocks and without stopping containers. `tests/cases.json` defines expected behavior and R IDs; pytest records observations/outcomes under `LAB5_RUN_DIR` (or a manual-tests directory). Parametrized inputs produce more executed tests than named case groups. Controlled failure cases are explicitly launched by the full suite rather than ordinary pytest.

## Full measured suite

```bash
.venv/bin/python scripts/run_suite.py
# Optional bounded exploration beyond the three mandatory levels:
.venv/bin/python scripts/run_suite.py --extended
```

The selected submission also includes `scripts/run_supplement.py`: a distinct 1600-user diagnostic
run preserving underlying transport exceptions, followed by an explicitly abrupt primary SIGKILL
scenario. It uses its own unique run directory and `supplementary-results.json`; the required
graceful-stop result remains unchanged. Run the supplement only after a completed main suite.
Its controlled crash always restarts the same node and verifies topology/data retention.

The suite performs functional tests, persistent-record inspection, API restart, a separate full MongoDB outage with POST/GET 503, normal load tests, api2 stop/start and an automatic primary election. It targets only project lab5 and restores controlled stops in finally blocks. A file lock prevents simultaneous suites. Each run writes `logs/runs/<unique-run-id>/`. Selected results are also copied to required `logs/` filenames; previous originals stay in their run directory. Runtime command output may be redirected to ignored `logs/live/`.

Do not run a second suite or generate unrelated traffic during measurements. Re-running creates additional test records; it does not drop databases or volumes. Previously confirmed records remain available. Comparison targets were committed in specification R48 before measurement: p95 <= 1,000 ms and failure rate <= 1% for aggregate and each endpoint at 10/50/100 users. These are self-selected local educational targets, not official instructor SLAs. Exploratory levels may intentionally exceed them and remain reported as FAIL.

## Reproduce each load level

All measured HTTP requests pass through nginx. The fixed mix is GET /time weight 3, POST /records weight 1, and 0.1-0.5 s think time. The suite warms up with 10 GETs and 10 writes outside the measured CSV. Locust's configured interval includes the ramp-up; stop-timeout allows in-flight requests to finish. Exact start/end times, user counts and commands are in the run summary. Raw per-request CSV records latency, status, hostname and record ID. Original periodic `*_stats.csv` files are preserved; `*_final_stats.csv` is exported directly by Locust's StatsCSV at its quit event after the runner finishes. The report uses that final native histogram and checks its request count against the complete raw CSV. This avoids silently using an earlier periodic snapshot that omits the final requests.

```bash
.venv/bin/python -m locust -f tests/locustfile.py --headless \
  -u 10 -r 5 -t 60s --host http://127.0.0.1:8080 --csv logs/manual_10
.venv/bin/python -m locust -f tests/locustfile.py --headless \
  -u 50 -r 10 -t 60s --host http://127.0.0.1:8080 --csv logs/manual_50
.venv/bin/python -m locust -f tests/locustfile.py --headless \
  -u 100 -r 20 -t 60s --host http://127.0.0.1:8080 --csv logs/manual_100
```

Use a fresh CSV prefix for every manual repeat. Set `LAB5_RAW_CSV` to an unused path to also capture every request. The runner records container CPU/memory, host memory/swap and generator CPU/RSS every few seconds. A closed-loop think-time workload is not an unlimited-arrival capacity benchmark. Report the measured range and observed constraints; do not infer a saturation point solely from a large user count.

## Failure demonstrations

The full suite automatically orchestrates the scenarios with timestamps. For an interactive demonstration, start the probe in one terminal and run the relevant commands in another:

```bash
.venv/bin/python tests/probe.py --scenario api_down --seconds 60 \
  --output logs/manual-probe-api.txt
docker compose stop api2
# Keep stopped approximately 20 seconds and inspect served_by responses.
docker compose start api2

docker compose exec mongo1 mongosh --quiet --eval "db.hello().primary"
# Stop the CURRENT primary from the answer, not a hardcoded assumed node:
docker compose stop <current-primary-service>
# Observe a new PRIMARY on a surviving node and successful writes before restart.
docker compose start <same-old-primary-service>
docker compose exec mongo1 mongosh --quiet --eval \
  "rs.status().members.map(m => m.name + ' ' + m.stateStr)"
```

Start a separate probe file for the primary scenario. Never manually promote MongoDB: the scenario verifies its automatic election. Probe files are timestamped JSON Lines, not preset responses; POST and GET probes are separate. The intended start interval is 0.5 s when requests are fast. A slow request extends the real interval, which is visible in start/end/elapsed fields. Failure detection/election samples have their own timestamps. Docker stop command start and completion bracket the observed stop rather than defining a fictional exact network-failure instant.

Recovery duration is calculated from actual probe events. If writes succeed throughout a graceful primary stop, the report records zero observed failed probes and the measured election rather than inventing a 503. A separate full-outage check establishes storage 503 behavior. A timeout/503 may leave the write outcome uncertain; only successful responses count as majority-acknowledged control records.

## Restore and inspect

After an interrupted manual scenario, start the specific stopped Lab 5 services. This preserves data:

```bash
docker compose start mongo1 mongo2 mongo3 api1 api2 api3 nginx
docker compose exec mongo1 mongosh --quiet /scripts/init-replica.js
docker compose exec mongo1 mongosh --quiet --eval \
  "rs.status().members.map(m => m.name + ' ' + m.stateStr)"
curl -i http://127.0.0.1:8080/time
```

Require one PRIMARY and two SECONDARY, then verify a saved record ID through nginx. Runtime logs stay in Docker; the evidence collector copies timestamped snapshots rather than following an actively changing tracked file. Do not reset roles to a chosen hostname or delete data to make a failed check pass.

## Specification, evidence and assessment

`spec.md` v4 preserves R1-R31 from the previous specification as applicable/historical requirements, and appends R32-R50 for Lab 5. The current image implements `/time`, `/echo` and `/records`; RustFS/Redis endpoints remain in the separate unchanged Lab 4 deployment. `test_report.md` provides traceable cases, original load numbers, failure timelines, CAP interpretation, two prioritized recommendations and all four reflection answers.

`screenshots/README.md` identifies image provenance and any unavailable captures. Browser views of archived logs are explicitly labelled as recorded evidence, never presented as a live terminal. Original machine-readable logs remain authoritative. `MANIFEST.sha256` verifies the submitted files and excludes itself.

To regenerate the report and static chart from the selected completed run:

```bash
.venv/bin/python -m pip install -r requirements-report.txt
.venv/bin/python scripts/verify_final.py
.venv/bin/python scripts/analyze_load.py
.venv/bin/python scripts/plot_results.py
.venv/bin/python scripts/build_report.py
.venv/bin/python scripts/build_evidence.py
```

Regenerating evidence pages does not recapture screenshots. Existing snapshots keep their original provenance. Refresh the manifest only after intentional updates to a submission.

The report generator reads the student's `Group:` from this README, so regenerating the report preserves the supplied group. Keep the metadata in README and `test_report.md` consistent. After intentional documentation updates, rebuild the ZIP and checksums with the standard-library packer (no third-party packages needed):

```bash
python3 scripts/package_submission.py --output /absolute/output/Serbina_Sofiya_Lab5.zip
```

The original Git remote reports that this same repository moved to `https://github.com/vesta-12/Lab4`; the old URL redirects. The Lab 5 branch is `https://github.com/vesta-12/Lab4/tree/lab5-nosql-fault-tolerance`.

Primary references: [MongoDB elections](https://www.mongodb.com/docs/manual/core/replica-set-elections/), [PyMongo operation timeouts](https://pymongo.readthedocs.io/en/4.10.1/examples/timeouts.html), [nginx upstream retry](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_next_upstream), [Locust documentation](https://docs.locust.io/en/2.32.4/).
