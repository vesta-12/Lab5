# Test Report - Lab 5

Student: Sofiya Serbina  
Group: ICT4401-ENG-1

Tested service: stateless Flask record API at http://127.0.0.1:8080.  
Environment: Docker Compose project lab5; three API copies, nginx, MongoDB rs0 with three nodes.  
Selected live run: `20261120T104224Z-425be5`, completed 2026-11-20T10:48:39.543740+00:00. Timestamps are UTC; add five hours for Almaty local time. No mocked responses are used.

The host has 8 GiB physical RAM; Docker reports 8 virtual CPUs and 4,106,604,544 bytes (about 3.825 GiB) of VM RAM. Existing Lab 4 containers remain running. Each MongoDB node has a 0.25 GiB WiredTiger cache. Each API has one Gunicorn worker and four threads. Python 3.9.6 runs requests/pytest/Locust on macOS; the API image uses Python 3.12. Exact versions, image digests and resources: [environment.json](logs/environment.json).

## 1. Test cases

All functional calls pass through nginx. The catalog contains 13 functional case groups (20 parametrized pytest executions) and four explicit persistence/failure cases. Preconditions: all seven core services ready; one PRIMARY and two SECONDARY; fresh UUIDs are generated without resetting the database. Source: [cases.json](tests/cases.json), [pytest.log](logs/pytest.log), [JUnit XML](logs/pytest.xml), [HTTP observations](logs/functional-http.jsonl).

| # | Requirement (spec.md) | Type | Input | Expected | Actual | Pass/Fail |
| --- | --- | --- | --- | --- | --- | --- |
| TC01 | R1, R42 | functional | GET /time through nginx | 200; server_time and served_by from api1/api2/api3 | 1/1 executions passed; HTTP 200 | PASS |
| TC02 | R2, R3 | functional/negative | POST /echo with message, then without it | 200 echo; missing message 400 | 1/1 executions passed; HTTP 200, 400 | PASS |
| TC03 | R33, R39 | functional | POST /records with valid text | 201; lowercase UUIDv4; text and served_by; Location | 1/1 executions passed; HTTP 201 | PASS |
| TC04 | R34 | functional | Create/read original Unicode text | 201 then 200; exact id and Unicode text | 1/1 executions passed; HTTP 200, 201 | PASS |
| TC05 | R34 | negative | GET a new nonexistent UUID | 404; record not found | 1/1 executions passed; HTTP 404 | PASS |
| TC06 | R35 | negative | Malformed and uppercase IDs | 400 JSON error | 2/2 executions passed; HTTP 400 | PASS |
| TC07 | R36 | negative | Missing, null, numeric, empty text; non-object JSON | 400 for all invalid inputs | 5/5 executions passed; HTTP 400 | PASS |
| TC08 | R36 | negative | Malformed JSON and text/plain input | 400 | 1/1 executions passed; HTTP 400 | PASS |
| TC09 | R37 | edge | ASCII and Unicode text at exactly 65,536 UTF-8 bytes | 201 then 200; exact original text | 2/2 executions passed; HTTP 200, 201 | PASS |
| TC10 | R37 | edge/negative | ASCII and Unicode text above 65,536 bytes | 400 | 2/2 executions passed; HTTP 400 | PASS |
| TC11 | R36, R37 | edge/negative | Lone surrogate Unicode; JSON body above 512 KiB | 400 JSON errors | 1/1 executions passed; HTTP 400 | PASS |
| TC12 | R40, R42 | integration | Create once; read twelve times through nginx | 200 exact shared record from at least two API copies | 1/1 executions passed; HTTP 200, 201; GET distribution {"api1": 4, "api2": 4, "api3": 4} | PASS |
| TC13 | R33 | functional | Create identical text twice | Two distinct UUIDs | 1/1 executions passed; HTTP 201 | PASS |
| TC14 | R38, R50 | failure | Explicit full-database-outage scenario; POST and GET | 503 in less than 12 s per request; /time 200; database restored | POST 503 in 4.415s; GET 503 in 4.506s; /time 200; replica set restored | PASS |
| TC15 | R40 | persistence | Stop/start api1 after creating a control record | Original data remains readable through other copies and after restart | Original control record readable while api1 stopped and after restart: PASS | PASS |
| TC16 | R43, R44, R50 | failure/load balancing | Probe; stop api2 for about 20 s; 30 GET /time while stopped; restart | No api2 response during stop; at least two live API copies; api2 returns; actual errors quantified | Stopped 20.003s; during {'api1': 15, 'api3': 15}; restored {'api2': 10, 'api1': 10, 'api3': 10} | PASS |
| TC17 | R45, R46, R50 | failure/persistence | Stop actual primary; probe and observe automatic election; restart old node | Different primary accepts writes before old node returns; control records retained; final 1 PRIMARY + 2 SECONDARY | mongo2 -> mongo1; 4 retained control IDs; final one PRIMARY/two SECONDARY | PASS |

**Pytest: 20 passed, 0 failed.** The four controlled cases are separately asserted by `scripts/run_suite.py`; they are not counted as extra pytest tests. Replica-set initialization was run twice: the second invocation verified the same configuration without reinitializing it. A MongoDB query independently found the control record. Evidence: [events.jsonl](logs/events.jsonl), [MongoDB record](logs/mongo-record.log), [client concerns](logs/mongo-client-config.log), [idempotency](logs/init-idempotency.log).

## 2. Load tests

Tool: Locust 2.32.4, fixed 3:1 GET `/time` to POST `/records`, with think time uniformly between 0.1 and 0.5 s. Ten GETs and ten writes warm up the service outside each measured run. Configured time includes user spawning; spawn rates are 5/10/20 users/s at 10/50/100 users. All target user counts were observed. Each request records its actual latency/status in a `*_requests.csv` file. POST success is HTTP 201, GET success is HTTP 200.

The report uses native Locust `*_final_stats.csv`, exported after runner shutdown using Locust StatsCSV. Every final request count equals the raw CSV row count and the console total. The original periodically written `*_stats.csv` is also preserved: its last snapshot can precede final requests. Histogram p95 is Locust's approximate percentile, not an average or a manually invented value. The initial run exposed this periodic/final difference and was retained under `logs/runs/`; measurements were rerun with a final exporter. The application and predefined R48 thresholds were unchanged.

Targets were committed in spec R48 before measurement: p95 <= 1,000 ms and failures <= 1% for each endpoint and aggregate at the three mandatory normal-load levels. They are self-selected educational targets, not instructor-provided SLAs. No RPS minimum was invented.

| Users | Duration | RPS | Median (p50), ms | p95, ms | Errors, % | Target from spec.md | Pass/Fail |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | 60 s | 31.803 | 4.000 | 13.000 | 0.000 | R48: p95 <=1000 ms; errors <=1% | PASS |
| 50 | 60 s | 158.970 | 3.000 | 7.000 | 0.000 | R48: p95 <=1000 ms; errors <=1% | PASS |
| 100 | 60 s | 317.683 | 3.000 | 7.000 | 0.000 | R48: p95 <=1000 ms; errors <=1% | PASS |
| 200 | 30 s | 616.709 | 2.000 | 8.000 | 0.000 | R48: p95 <=1000 ms; errors <=1% | PASS |
| 400 | 30 s | 1219.795 | 2.000 | 32.000 | 0.000 | R48: p95 <=1000 ms; errors <=1% | PASS |
| 800 | 30 s | 2019.078 | 37.000 | 190.000 | 0.391 | R48: p95 <=1000 ms; errors <=1% | PASS |
| 1600 | 30 s | 1874.423 | 140.000 | 430.000 | 5.505 | R48: p95 <=1000 ms; errors <=1% | FAIL |

Levels above 100 users are explicitly exploratory, use 30 s rather than 60 s, and keep the same workload/server configuration. They are not substituted for the three mandatory 60 s levels. Target breaches remain visible rather than changing the target.

| Users | Endpoint | Requests | Failures | RPS | Median (p50), ms | p95, ms |
| --- | --- | --- | --- | --- | --- | --- |
| 10 | POST /records | 499 | 0 | 8.344 | 8 | 18 |
| 10 | GET /time | 1403 | 0 | 23.459 | 3 | 9 |
| 10 | Aggregated | 1902 | 0 | 31.803 | 4 | 13 |
| 50 | POST /records | 2344 | 0 | 39.150 | 4 | 10 |
| 50 | GET /time | 7174 | 0 | 119.821 | 2 | 5 |
| 50 | Aggregated | 9518 | 0 | 158.970 | 3 | 7 |
| 100 | POST /records | 4744 | 0 | 79.316 | 4 | 10 |
| 100 | GET /time | 14257 | 0 | 238.367 | 2 | 5 |
| 100 | Aggregated | 19001 | 0 | 317.683 | 3 | 7 |
| 200 | POST /records | 4723 | 0 | 158.300 | 3 | 13 |
| 200 | GET /time | 13677 | 0 | 458.409 | 2 | 6 |
| 200 | Aggregated | 18400 | 0 | 616.709 | 2 | 8 |
| 400 | POST /records | 9201 | 0 | 307.877 | 4 | 43 |
| 400 | GET /time | 27253 | 0 | 911.919 | 2 | 26 |
| 400 | Aggregated | 36454 | 0 | 1219.795 | 2 | 32 |
| 800 | POST /records | 15165 | 58 | 506.816 | 41 | 200 |
| 800 | GET /time | 45250 | 178 | 1512.261 | 36 | 190 |
| 800 | Aggregated | 60415 | 236 | 2019.078 | 37 | 190 |
| 1600 | POST /records | 14251 | 771 | 467.761 | 150.0 | 420 |
| 1600 | GET /time | 42856 | 2373 | 1406.663 | 140.0 | 440 |
| 1600 | Aggregated | 57107 | 3144 | 1874.423 | 140.0 | 430 |

Commands (run from `lab5/`; the actual absolute CSV paths, raw/final CSV environment settings and wall-clock start/end are in [results.json](logs/results.json)):

```bash
.venv/bin/python -m locust -f tests/locustfile.py --headless -u 10 -r 5 -t 60s --host http://127.0.0.1:8080 --csv logs/repeat_10 --csv-full-history --stop-timeout 12 --only-summary
```

```bash
.venv/bin/python -m locust -f tests/locustfile.py --headless -u 50 -r 10 -t 60s --host http://127.0.0.1:8080 --csv logs/repeat_50 --csv-full-history --stop-timeout 12 --only-summary
```

```bash
.venv/bin/python -m locust -f tests/locustfile.py --headless -u 100 -r 20 -t 60s --host http://127.0.0.1:8080 --csv logs/repeat_100 --csv-full-history --stop-timeout 12 --only-summary
```

```bash
.venv/bin/python -m locust -f tests/locustfile.py --headless -u 200 -r 40 -t 30s --host http://127.0.0.1:8080 --csv logs/repeat_200 --csv-full-history --stop-timeout 12 --only-summary
```

```bash
.venv/bin/python -m locust -f tests/locustfile.py --headless -u 400 -r 80 -t 30s --host http://127.0.0.1:8080 --csv logs/repeat_400 --csv-full-history --stop-timeout 12 --only-summary
```

```bash
.venv/bin/python -m locust -f tests/locustfile.py --headless -u 800 -r 160 -t 30s --host http://127.0.0.1:8080 --csv logs/repeat_800 --csv-full-history --stop-timeout 12 --only-summary
```

```bash
.venv/bin/python -m locust -f tests/locustfile.py --headless -u 1600 -r 320 -t 30s --host http://127.0.0.1:8080 --csv logs/repeat_1600 --csv-full-history --stop-timeout 12 --only-summary
```

For exact final/raw exports use `scripts/run_suite.py --extended`; a fresh unique directory is created automatically. Normal failures are measured outside these load runs. Each original command, Locust console log, history CSV, failures CSV and resource sample is retained.

| Users | Samples | Generator peak CPU % | Max API CPU % | Max Mongo CPU % | nginx CPU % | Min host available MiB |
| --- | --- | --- | --- | --- | --- | --- |
| 10 | 12 | 16.400 | 3.780 | 41.560 | 1.370 | 1065.234 |
| 50 | 12 | 22.300 | 10.580 | 56.040 | 1.890 | 1153.859 |
| 100 | 12 | 37.900 | 17.580 | 60.120 | 3.970 | 1149.375 |
| 200 | 6 | 48.800 | 28.130 | 70.030 | 6.920 | 1188.953 |
| 400 | 6 | 62.000 | 39.450 | 48.740 | 13.110 | 1149.469 |
| 800 | 6 | 96.900 | 50.420 | 108.600 | 21.890 | 1150.281 |
| 1600 | 6 | 94.700 | 41.940 | 98.890 | 20.910 | 1176.234 |

CPU 100% means approximately one CPU core for process/container counters. Samples occur every few seconds and can miss short peaks. Host memory/swap and existing Lab 4 containers are retained in the original resource JSONL. All components share one Mac, so these are local end-to-end results, not an isolated production-capacity benchmark.

![Measured load results](logs/load-results.png)

## 3. Fault tolerance & load balancing

| Phase | Requests | Actual served_by distribution | HTTP errors |
| --- | --- | --- | --- |
| Baseline | 30 | {"api3": 10, "api1": 10, "api2": 10} | 0 |
| api2 stopped | 30 | {"api1": 15, "api3": 15} | 0 |
| api2 restarted | 30 | {"api2": 10, "api1": 10, "api3": 10} | 0 |
| Final | 30 | {"api2": 10, "api1": 10, "api3": 10} | 0 |

Each row is a separate set of exactly 30 requests, not a projected distribution. Full rows and statuses are in `logs/distribution-*.json`.

### Scenario 1 - service replica stopped

A write probe and an independent GET probe were active before, during and after stopping api2. The stop command began at 2026-11-20T10:47:43.371761+00:00 and completed at 2026-11-20T10:47:44.888762+00:00. Restart began at 2026-11-20T10:48:04.891691+00:00. The measured stopped interval between command completion and restart start was 20.003 s. api2 did not appear in the stopped-node distribution and returned after restart.

| Probe | All samples | HTTP 503 after stop | Other HTTP errors | Transport errors |
| --- | --- | --- | --- | --- |
| POST /records | 70 | 0 | 0 | 0 |
| GET control record | 70 | 0 | 0 | 0 |

The control record remained readable. Source: [write probe](logs/probe_api_down.txt), [read probe](logs/probe_api_down_reads.txt). nginx retries eligible connection/timeout/502 failures on other upstreams, bounded to three tries; it does not retry arbitrary delivered POSTs or hide storage 503 responses.

### Scenario 2 - MongoDB primary stopped

The dynamically discovered primary was **mongo2**. A surviving member reported **mongo1** as the new primary while the old node remained stopped. A majority write and reads of all 4 control IDs succeeded before restarting the old node. No manual promotion or replica-set reconfiguration was performed.

| Event | Time / Value |
| --- | --- |
| Stop command started | 2026-11-20T10:48:19.083795+00:00 |
| Stop command completed | 2026-11-20T10:48:24.353075+00:00 |
| First observed write error (response end) | Not observed |
| First HTTP 503 (write response end) | Not observed |
| Write HTTP 503 count | 0 |
| Write other HTTP errors | 0 |
| Write transport errors | 0 |
| Read HTTP 503 count | 0 |
| Read other HTTP errors | 0 |
| Read transport errors | 0 |
| New primary detected | 2026-11-20T10:48:24.779459+00:00 |
| Observed stop-to-primary-detection, s | 5.696 |
| First successful write after error interval | Not observed |
| Observed stop-to-write-recovery, s | Not observed |
| First-error-response-to-write-recovery, s | Not observed |
| First successful post-stop write | 2026-11-20T10:48:19.151887+00:00 |
| Old node restart command | 2026-11-20T10:48:30.807943+00:00 |
| Control-record retention | PASS |
| Final roles | mongo1:27017 PRIMARY, mongo2:27017 SECONDARY, mongo3:27017 SECONDARY |

Probe requests have actual start/end timestamps and latency. Requests started before the stop command are excluded from the post-stop error classification. Recovery after errors uses the first successful request started after the last failed response. If no failed write probe is observed, the outage fields remain Not observed; successful driver waiting or a fast graceful-stop election must not be turned into fictional 503s. Primary detection is sampled through mongosh, so its duration includes polling/command overhead. The independent read-probe errors and timings are retained as well.

Sources: [write probe](logs/probe_primary_down.txt), [read probe](logs/probe_primary_down_reads.txt), [timestamped commands](logs/events.jsonl), [complete result](logs/results.json).

**CAP interpretation.** Under the configured primary/majority policy, the minority side of a partition cannot acknowledge majority writes. A primary must be selected before this API can route primary reads and writes; losing one of three members still leaves a voting majority that can elect a leader and resume work. The experiment measures a node stop and its observed availability gap; it is not by itself a direct network-partition proof of CAP. The separate all-node outage produced POST and GET 503 in 4.415/4.506 s while /time remained 200. Four-second driver timeouts are budgets, with additional HTTP/scheduling overhead. A timed-out write can have an uncertain outcome; only successful responses were used as acknowledged control records.

### Supplement - abrupt primary crash (separate from the required graceful stop)

Supplement run `20261120T105045Z-8235fc` retained the required zero-error graceful handoff above and additionally sent SIGKILL only to the dynamically identified Lab 5 primary. This is an explicit crash scenario, not a replacement of the stop result. A new primary accepted writes before the crashed node was restarted. All control records remained readable after recovery.

| Crash event | Actual time / value |
| --- | --- |
| Old primary / new primary | mongo1 / mongo2 |
| SIGKILL command started | 2026-11-20T10:51:30.883460+00:00 |
| First write error | 2026-11-20T10:51:35.637086+00:00 |
| First HTTP 503 | 2026-11-20T10:51:35.637086+00:00 |
| Write HTTP 503 / other HTTP / transport errors | 2 / 0 / 0 |
| Read HTTP 503 / other HTTP / transport errors | 2 / 0 / 0 |
| New primary observed | 2026-11-20T10:51:41.863745+00:00 |
| Observed stop-to-primary-detection seconds | 10.980 |
| First successful write after errors | 2026-11-20T10:51:41.346349+00:00 |
| Observed stop-to-write-recovery seconds | 10.463 |
| First-error-to-write-recovery seconds | 5.709 |
| Crashed node restart started | 2026-11-20T10:51:47.878309+00:00 |
| Final roles | mongo1:27017 SECONDARY, mongo2:27017 PRIMARY, mongo3:27017 SECONDARY |
| Acknowledged control-record retention | PASS |

Sources: [crash write probe](logs/probe_primary_crash.txt), [crash read probe](logs/probe_primary_crash_reads.txt), [supplement events](logs/supplement-events.jsonl), [supplement result](logs/supplementary-results.json). The abrupt failure removes the opportunity for a graceful handoff and makes the observed client error interval distinct from the required Docker stop test.

## 4. Conclusions & recommendations

At 10 users, throughput was 31.803 RPS with p95 13 ms; at 100 users it was 317.683 RPS with p95 7 ms. The highest tested level was 1600 users: 1874.423 RPS, p95 430 ms, failures 5.505%. Relative throughput per user versus the 100-user level was 36.9%.

The first explored R48 target breach occurred at 1600 users. This is an observed local operating limit for the selected workload, not an exact universal saturation capacity. A target can fail for one endpoint even if the aggregate passes. Its original per-endpoint numbers remain above; the target was not changed after testing.

At the 800-user level, 236 failures were transport failures represented by Locust status 0 (no HTTP response), not an HTTP status code returned by the application. The original error labels were generic; the supplementary high-load run preserved underlying transport exceptions rather than replacing them with expected-status labels. See [transport diagnostics](logs/bottleneck-analysis.json).

**Evidence-supported limit:** No nginx worker-connection-limit message was logged. Remote disconnect/reset errors establish an ingress/connection-path failure; shared generator/host/VM contention remains a hypothesis requiring isolation. From 800 to 1600 users throughput changed by -7.16% despite doubling users; latency and transport failure rate increased. This establishes saturation/degradation of the tested end-to-end arrangement in that range, while a single server-side causal bottleneck is not proven. The generator approached one full CPU core in the resource samples, making an isolated generator/ingress comparison the first diagnostic priority.

The `_id` lookup already uses MongoDB's existing primary-key index. Record writes add database/majority work that /time does not perform; endpoint latency differences alone do not prove that MongoDB is the bottleneck. Compare the measured API, MongoDB, nginx and generator CPU columns. Shared VM/host limits and the fixed twelve API threads are plausible constraints; confirming a single causal bottleneck requires a controlled one-variable comparison. The sampled resource data bounds the conclusion rather than inventing an unsupported cause.

**Priority 1 - isolate the generator and modernize its Python runtime.** Run the same fixed workload from a separate machine or reserved CPU resources with supported Python/OpenSSL. This removes contention between the generator, Docker and desktop applications, and addresses the recorded Python 3.9/LibreSSL warnings (current traffic is local HTTP). Expected impact: a more reliable server-capacity estimate and less generator-induced latency; no improvement percentage is claimed without measurement.

**Priority 2 - tune API concurrency within the measured memory/CPU budget.** Compare the current one-worker/four-thread API with one controlled alternative, for example two workers with bounded threads and pools, while keeping MongoDB concerns, request mix and nginx policy unchanged. Expected impact: less application queueing if the workers are the active constraint; extra processes can also raise memory/CPU pressure, so retain only a measured improvement. Do not weaken majority acknowledgement to make benchmark numbers look better.

**Re-test after each change:** repeat the 10/50/100-user 60 s runs and the highest exploratory level with the same warm-up/ramp and multiple repetitions; compare both endpoint and aggregate p95, RPS, error rate, CPU and memory. Repeat TC14-TC17 to verify that performance tuning preserves 503 handling, balancing, automatic election and acknowledged-record retention.

## 5. Reflection questions

### 1. Why does MongoDB stop accepting writes when the primary fails, and what CAP choice is involved?

Writes require an elected primary and majority acknowledgement in this configuration. The surviving two members elect a new primary; probes and the timeline above show what clients actually observed. Under a partition, a minority cannot confirm majority writes, prioritizing the configured consistency guarantees over minority write availability. A node-stop test illustrates recovery, while CAP specifically concerns partitions.

### 2. How does reading from a primary differ from a secondary?

This API chooses primary reads with majority read concern. Secondary reads can distribute read load and keep some reads available during a primary problem, but replication lag can return stale data. They are suitable for delay-tolerant analytics and less suitable for immediately confirming a user's update. Majority writes alone do not imply linearizable reads or eliminate all failover uncertainty.

### 3. What does nginx do when one service copy stops?

The api2-down distribution above excludes api2 and shows the remaining copies responding. `max_fails=1` counts a qualifying unsuccessful attempt during `fail_timeout=5s`; the node is temporarily unavailable for that period. `proxy_next_upstream error timeout http_502` allows an eligible request to try another upstream, with at most three tries. Requests already delivered cannot all be safely replayed; `non_idempotent` is not enabled. Docker DNS resolution lets a returning or recreated hostname be resolved again.

### 4. Why must the service be stateless?

nginx can send creation and reading to different API copies. TC12 confirms this with real requests. Shared records must live in MongoDB, not one API's memory/disk, so a stopped API does not own the only copy of data. In Lab 4, Redis required manual replica promotion, application redirection and reconciliation. Here MongoDB's voting replica set elects a new primary and PyMongo discovers it from the seed list without changing application source or manually promoting a node.

## Screenshots and Evidence

Images 01-11 are genuine browser captures of explicitly labelled archived log evidence, not new Terminal screenshots or live replays. Image 12 captures a live record response through nginx. Original logs and CSVs remain the authoritative measurements; full provenance is in [screenshots/README.md](screenshots/README.md).

| Evidence | Screenshot |
| --- | --- |
| MongoDB replica set | [Replica set](screenshots/01_replica_set.jpg) |
| Docker Compose | [Services](screenshots/02_compose.jpg) |
| Record creation and reading | [POST and GET](screenshots/03_records.jpg) |
| nginx distribution | [30 requests](screenshots/04_distribution.jpg) |
| API failure | [api2 stopped](screenshots/05_api_down.jpg) |
| Load tests | [10 users](screenshots/06_load_10.jpg), [50 users](screenshots/07_load_50.jpg), [100 users](screenshots/08_load_100.jpg) |
| MongoDB automatic election | [Graceful primary stop](screenshots/09_primary_down.jpg) |
| Restored topology | [Final roles](screenshots/10_final_roles.jpg) |
| Abrupt primary crash | [Crash and recovery](screenshots/11_primary_crash.jpg) |
| Live record | [Live API response](screenshots/12_live_record.jpg) |

## Evidence and references

The submitted screenshots are identified individually in [screenshots/README.md](screenshots/README.md). Archived-log browser captures are labelled as such and do not impersonate a live terminal. All underlying logs/CSVs accompany them. Final state is checked in [final-verification.json](logs/final-verification.json); file integrity is recorded in `MANIFEST.sha256`.

Primary documentation: [MongoDB elections](https://www.mongodb.com/docs/manual/core/replica-set-elections/), [PyMongo timeout semantics](https://pymongo.readthedocs.io/en/4.10.1/examples/timeouts.html), [nginx retry conditions](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_next_upstream), [nginx DNS resolution](https://nginx.org/en/docs/http/ngx_http_upstream_module.html#resolve), [Locust 2.32.4](https://docs.locust.io/en/2.32.4/).
