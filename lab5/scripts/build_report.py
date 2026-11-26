#!/usr/bin/env python3
"""Build the assessed Markdown report from selected real-run evidence only."""
from collections import Counter
from datetime import datetime,timezone
import csv
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
LOG=ROOT/'logs'

def lines(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x]

def value(x):
    if x is None: return 'Not observed'
    if isinstance(x,float): return '{:.3f}'.format(x)
    return str(x).replace('|',' / ').replace('\n',' ')

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+
                     ['| '+' | '.join(value(x) for x in row)+' |' for row in rows])

def stamp(row):
    return row['end_utc'] if row else None

def student_group():
    """Use supplied README metadata; never invent a group on regeneration."""
    match=re.search(r'\bGroup:\s*([^\r\n]+)',(ROOT/'README.md').read_text())
    return match.group(1).strip().rstrip('.') if match else 'Not provided'

def screenshot_evidence():
    evidence=[
      ('MongoDB replica set',[('Replica set','01_replica_set.jpg')]),
      ('Docker Compose',[('Services','02_compose.jpg')]),
      ('Record creation and reading',[('POST and GET','03_records.jpg')]),
      ('nginx distribution',[('30 requests','04_distribution.jpg')]),
      ('API failure',[('api2 stopped','05_api_down.jpg')]),
      ('Load tests',[('10 users','06_load_10.jpg'),('50 users','07_load_50.jpg'),('100 users','08_load_100.jpg')]),
      ('MongoDB automatic election',[('Graceful primary stop','09_primary_down.jpg')]),
      ('Restored topology',[('Final roles','10_final_roles.jpg')]),
      ('Abrupt primary crash',[('Crash and recovery','11_primary_crash.jpg')]),
      ('Live record',[('Live API response','12_live_record.jpg')]),
    ]
    rows=[]
    for description,images in evidence:
        for _label,name in images:
            assert (ROOT/'screenshots'/name).is_file(),'Missing evidence image: '+name
        rows.append([description,', '.join('['+label+'](screenshots/'+name+')' for label,name in images)])
    return ['## Screenshots and Evidence',
      'Images 01-11 are genuine browser captures of explicitly labelled archived log evidence, '
      'not new Terminal screenshots or live replays. Image 12 captures a live record response '
      'through nginx. Original logs and CSVs remain the authoritative measurements; full '
      'provenance is in [screenshots/README.md](screenshots/README.md).',
      table(['Evidence','Screenshot'],rows)]

def resources(level):
    file=LOG/('locust_'+str(level['users'])+'_resources.jsonl')
    samples=lines(file)
    peak={}; generator=0; available=None; swap=0
    for sample in samples:
        generator=max(generator,sample.get('generator_cpu_percent',0))
        available=min(available if available is not None else float('inf'),sample['host_available_bytes'])
        swap=max(swap,sample.get('host_swap_used_bytes',0))
        for row in sample.get('docker',[]):
            name=row.get('Name','')
            if name.startswith('lab5-'):
                cpu=float(row.get('CPUPerc','0%').strip('%'))
                peak[name]=max(peak.get(name,0),cpu)
    return {'samples':len(samples),'peak_cpu':peak,'generator_peak_cpu':generator,
            'minimum_host_available_mib':(available or 0)/1024**2,'peak_host_swap_mib':swap/1024**2}

def main():
    result=json.loads((LOG/'results.json').read_text())
    supplement=json.loads((LOG/'supplementary-results.json').read_text()) if (LOG/'supplementary-results.json').exists() else {}
    assert not supplement or supplement['complete']
    assert result['complete'] is True,'Do not report an incomplete run as successful'
    assert result['functional']['failed']==0
    catalog=json.loads((ROOT/'tests/cases.json').read_text())
    observations=lines(LOG/'functional-http.jsonl')
    outcomes=lines(LOG/'functional-results.jsonl')
    env=json.loads((LOG/'environment.json').read_text())
    all_load=result['load']+result.get('exploratory_load',[])+supplement.get('diagnostic_load',[])
    summary_resources={str(x['users']):resources(x) for x in all_load}
    (LOG/'resource-summary.json').write_text(json.dumps(summary_resources,indent=2)+'\n')
    report=['# Test Report - Lab 5','Student: Sofiya Serbina  \nGroup: '+student_group(),
      'Tested service: stateless Flask record API at '+result['base_url']+'.  \n'
      'Environment: Docker Compose project lab5; three API copies, nginx, MongoDB rs0 with three nodes.  \n'
      'Selected live run: `'+result['run_id']+'`, completed '+result['completed_utc']+'. '
      'Timestamps are UTC; add five hours for Almaty local time. No mocked responses are used.',
      'The host has 8 GiB physical RAM; Docker reports 8 virtual CPUs and 4,106,604,544 bytes '
      '(about 3.825 GiB) of VM RAM. Existing Lab 4 containers remain running. Each MongoDB node '
      'has a 0.25 GiB WiredTiger cache. Each API has one Gunicorn worker and four threads. '+
      env['test_python']+' runs requests/pytest/Locust on macOS; the API image uses Python 3.12. '
      'Exact versions, image digests and resources: [environment.json](logs/environment.json).',
      '## 1. Test cases',
      'All functional calls pass through nginx. The catalog contains 13 functional case groups '
      '(20 parametrized pytest executions) and four explicit persistence/failure cases. '
      'Preconditions: all seven core services ready; one PRIMARY and two SECONDARY; fresh UUIDs '
      'are generated without resetting the database. Source: [cases.json](tests/cases.json), '
      '[pytest.log](logs/pytest.log), [JUnit XML](logs/pytest.xml), '
      '[HTTP observations](logs/functional-http.jsonl).']
    case_rows=[]
    for case in catalog[:13]:
        selected=[x for x in outcomes if case['id']+'_' in x['test']]
        actual=[x for x in observations if case['id']+'_' in x['test']]
        statuses=sorted({x['status'] for x in actual})
        passed=sum(x['outcome']=='passed' for x in selected)
        text='{}/{} executions passed; HTTP {}'.format(passed,len(selected),', '.join(map(str,statuses)))
        if case['id']=='TC12':
            hosts=Counter(x['body']['served_by'] for x in actual if x['method']=='GET')
            text+='; GET distribution '+json.dumps(hosts)
        case_rows.append([case['id'],case['requirements'],case['type'],case['input'],case['expected'],text,
                          'PASS' if selected and passed==len(selected) else 'FAIL'])
    outage=result['full_database_outage']; api=result['api_failure']; mongo=result['primary_failure']
    extra=[
      ['POST 503 in {:.3f}s; GET 503 in {:.3f}s; /time 200; replica set restored'.format(outage['write_seconds'],outage['read_seconds']),'PASS'],
      ['Original control record readable while api1 stopped and after restart: '+result['api_restart_persistence'],'PASS'],
      ['Stopped {:.3f}s; during {}; restored {}'.format(api['stopped_seconds'],api['during_distribution']['counts'],api['after_distribution']['counts']),'PASS'],
      ['{} -> {}; {} retained control IDs; final one PRIMARY/two SECONDARY'.format(mongo['old_primary'],mongo['new_primary'],len(mongo['retained_control_ids'])),'PASS']]
    for case,actual in zip(catalog[13:],extra):
        case_rows.append([case['id'],case['requirements'],case['type'],case['input'],case['expected'],actual[0],actual[1]])
    report += [table(['#','Requirement (spec.md)','Type','Input','Expected','Actual','Pass/Fail'],case_rows),
      '**Pytest: {} passed, {} failed.** The four controlled cases are separately asserted by '
      '`scripts/run_suite.py`; they are not counted as extra pytest tests. Replica-set initialization '
      'was run twice: the second invocation verified the same configuration without reinitializing it. '
      'A MongoDB query independently found the control record. Evidence: '
      '[events.jsonl](logs/events.jsonl), [MongoDB record](logs/mongo-record.log), '
      '[client concerns](logs/mongo-client-config.log), [idempotency](logs/init-idempotency.log).'.format(result['functional']['passed'],result['functional']['failed']),
      '## 2. Load tests',
      'Tool: Locust 2.32.4, fixed 3:1 GET `/time` to POST `/records`, with think time uniformly '
      'between 0.1 and 0.5 s. Ten GETs and ten writes warm up the service outside each measured run. '
      'Configured time includes user spawning; spawn rates are 5/10/20 users/s at 10/50/100 users. '
      'All target user counts were observed. Each request records its actual latency/status in a '
      '`*_requests.csv` file. POST success is HTTP 201, GET success is HTTP 200.',
      'The report uses native Locust `*_final_stats.csv`, exported after runner shutdown using '
      'Locust StatsCSV. Every final request count equals the raw CSV row count and the console total. '
      'The original periodically written `*_stats.csv` is also preserved: its last snapshot can '
      'precede final requests. Histogram p95 is Locust\'s approximate percentile, not an average or '
      'a manually invented value. The initial run exposed this periodic/final difference and was '
      'retained under `logs/runs/`; measurements were rerun with a final exporter. The application '
      'and predefined R48 thresholds were unchanged.',
      'Targets were committed in spec R48 before measurement: p95 <= 1,000 ms and failures <= 1% '
      'for each endpoint and aggregate at the three mandatory normal-load levels. They are '
      'self-selected educational targets, not instructor-provided SLAs. No RPS minimum was invented.']
    load_rows=[]
    for x in all_load:
        load_rows.append([x['users'],str(x['duration_configured_seconds'])+' s',x['rps'],x['median_ms'],
          x['p95_ms'],x['error_percent'],'R48: p95 <=1000 ms; errors <=1%',
          'PASS' if x['targets_pass'] else 'FAIL'])
    report += [table(['Users','Duration','RPS','Median (p50), ms','p95, ms','Errors, %','Target from spec.md','Pass/Fail'],load_rows)]
    if result.get('exploratory_load'):
        report.append('Levels above 100 users are explicitly exploratory, use 30 s rather than 60 s, '
          'and keep the same workload/server configuration. They are not substituted for the three '
          'mandatory 60 s levels. Target breaches remain visible rather than changing the target.')
    detail=[]
    for x in all_load:
        for row in x['stats']:
            detail.append([x['users'],(row['Type']+' '+row['Name']).strip(),row['Request Count'],
              row['Failure Count'],float(row['Requests/s']),row['Median Response Time'],row['95%']])
    report += [table(['Users','Endpoint','Requests','Failures','RPS','Median (p50), ms','p95, ms'],detail),
      'Commands (run from `lab5/`; the actual absolute CSV paths, raw/final CSV environment settings '
      'and wall-clock start/end are in [results.json](logs/results.json)):']
    for x in all_load:
        report.append('```bash\n.venv/bin/python -m locust -f tests/locustfile.py --headless '
          '-u {} -r {} -t {}s --host {} --csv logs/repeat_{} '
          '--csv-full-history --stop-timeout 12 --only-summary\n```'.format(x['users'],x['spawn_rate'],
             x['duration_configured_seconds'],result['base_url'],x['users']))
    report.append('For exact final/raw exports use `scripts/run_suite.py --extended`; a fresh unique '
      'directory is created automatically. Normal failures are measured outside these load runs. '
      'Each original command, Locust console log, history CSV, failures CSV and resource sample is retained.')
    resource_rows=[]
    for x in all_load:
        r=summary_resources[str(x['users'])]
        resource_rows.append([x['users'],r['samples'],r['generator_peak_cpu'],
          max((v for k,v in r['peak_cpu'].items() if '-api' in k),default=0),
          max((v for k,v in r['peak_cpu'].items() if '-mongo' in k),default=0),
          max((v for k,v in r['peak_cpu'].items() if '-nginx' in k),default=0),r['minimum_host_available_mib']])
    report += [table(['Users','Samples','Generator peak CPU %','Max API CPU %','Max Mongo CPU %','nginx CPU %','Min host available MiB'],resource_rows),
      'CPU 100% means approximately one CPU core for process/container counters. Samples occur every '
      'few seconds and can miss short peaks. Host memory/swap and existing Lab 4 containers are '
      'retained in the original resource JSONL. All components share one Mac, so these are local '
      'end-to-end results, not an isolated production-capacity benchmark.',
      '![Measured load results](logs/load-results.png)',
      '## 3. Fault tolerance & load balancing',
      table(['Phase','Requests','Actual served_by distribution','HTTP errors'],[
        ['Baseline',30,json.dumps(result['baseline_distribution']['counts']),0],
        ['api2 stopped',30,json.dumps(api['during_distribution']['counts']),0],
        ['api2 restarted',30,json.dumps(api['after_distribution']['counts']),0],
        ['Final',30,json.dumps(result['final_distribution']['counts']),0]]),
      'Each row is a separate set of exactly 30 requests, not a projected distribution. Full rows '
      'and statuses are in `logs/distribution-*.json`.',
      '### Scenario 1 - service replica stopped',
      'A write probe and an independent GET probe were active before, during and after stopping '
      'api2. The stop command began at '+api['stop']['start_utc']+' and completed at '+api['stop']['end_utc']+
      '. Restart began at '+api['start']['start_utc']+'. The measured stopped interval between '
      'command completion and restart start was {:.3f} s. api2 did not appear in the stopped-node '
      'distribution and returned after restart.'.format(api['stopped_seconds']),
      table(['Probe','All samples','HTTP 503 after stop','Other HTTP errors','Transport errors'],[
        [name,api[key]['samples'],api[key]['http_503'],api[key]['other_http_errors'],api[key]['transport_errors']]
        for name,key in [('POST /records','writes'),('GET control record','reads')]]),
      'The control record remained readable. Source: [write probe](logs/probe_api_down.txt), '
      '[read probe](logs/probe_api_down_reads.txt). nginx retries eligible connection/timeout/502 '
      'failures on other upstreams, bounded to three tries; it does not retry arbitrary delivered '
      'POSTs or hide storage 503 responses.',
      '### Scenario 2 - MongoDB primary stopped',
      'The dynamically discovered primary was **'+mongo['old_primary']+'**. A surviving member '
      'reported **'+mongo['new_primary']+'** as the new primary while the old node remained stopped. '
      'A majority write and reads of all {} control IDs succeeded before restarting the old node. '
      'No manual promotion or replica-set reconfiguration was performed.'.format(len(mongo['retained_control_ids']))]
    w=mongo['writes']; rd=mongo['reads']
    report += [table(['Event','Time / Value'],[
      ['Stop command started',mongo['stop']['start_utc']],['Stop command completed',mongo['stop']['end_utc']],
      ['First observed write error (response end)',stamp(w['first_error'])],
      ['First HTTP 503 (write response end)',stamp(w['first_503'])],
      ['Write HTTP 503 count',w['http_503']],['Write other HTTP errors',w['other_http_errors']],
      ['Write transport errors',w['transport_errors']],['Read HTTP 503 count',rd['http_503']],
      ['Read other HTTP errors',rd['other_http_errors']],['Read transport errors',rd['transport_errors']],
      ['New primary detected',mongo['new_primary_observation']['timestamp']],
      ['Observed stop-to-primary-detection, s',mongo['observed_election_seconds']],
      ['First successful write after error interval',stamp(w['first_success_after_errors'])],
      ['Observed stop-to-write-recovery, s',w['stop_to_recovery_seconds']],
      ['First-error-response-to-write-recovery, s',w['error_to_recovery_seconds']],
      ['First successful post-stop write',stamp(w['first_post_stop_success'])],
      ['Old node restart command',mongo['start']['start_utc']],
      ['Control-record retention',mongo['retention']],
      ['Final roles',', '.join(x['name']+' '+x['state'] for x in mongo['final_members'])]]),
      'Probe requests have actual start/end timestamps and latency. Requests started before the '
      'stop command are excluded from the post-stop error classification. Recovery after errors '
      'uses the first successful request started after the last failed response. If no failed '
      'write probe is observed, the outage fields remain Not observed; successful driver waiting '
      'or a fast graceful-stop election must not be turned into fictional 503s. Primary detection '
      'is sampled through mongosh, so its duration includes polling/command overhead. The '
      'independent read-probe errors and timings are retained as well.',
      'Sources: [write probe](logs/probe_primary_down.txt), [read probe](logs/probe_primary_down_reads.txt), '
      '[timestamped commands](logs/events.jsonl), [complete result](logs/results.json).',
      '**CAP interpretation.** Under the configured primary/majority policy, the minority side of a '
      'partition cannot acknowledge majority writes. A primary must be selected before this API '
      'can route primary reads and writes; losing one of three members still leaves a voting '
      'majority that can elect a leader and resume work. The experiment measures a node stop and '
      'its observed availability gap; it is not by itself a direct network-partition proof of CAP. '
      'The separate all-node outage produced POST and GET 503 in {:.3f}/{:.3f} s while /time remained '
      '200. Four-second driver timeouts are budgets, with additional HTTP/scheduling overhead. '
      'A timed-out write can have an uncertain outcome; only successful responses were used as '
      'acknowledged control records.'.format(outage['write_seconds'],outage['read_seconds']),
      '## 4. Conclusions & recommendations']
    if supplement.get('primary_crash'):
        c=supplement['primary_crash']; cw=c['writes']; cr=c['reads']
        crash_section=[
          '### Supplement - abrupt primary crash (separate from the required graceful stop)',
          'Supplement run `'+supplement['run_id']+'` retained the required zero-error graceful '
          'handoff above and additionally sent SIGKILL only to the dynamically identified Lab 5 '
          'primary. This is an explicit crash scenario, not a replacement of the stop result. '
          'A new primary accepted writes before the crashed node was restarted. All control '
          'records remained readable after recovery.',
          table(['Crash event','Actual time / value'],[
            ['Old primary / new primary',c['old_primary']+' / '+c['new_primary']],
            ['SIGKILL command started',c['stop']['start_utc']],
            ['First write error',stamp(cw['first_error'])],
            ['First HTTP 503',stamp(cw['first_503'])],
            ['Write HTTP 503 / other HTTP / transport errors',str(cw['http_503'])+' / '+str(cw['other_http_errors'])+' / '+str(cw['transport_errors'])],
            ['Read HTTP 503 / other HTTP / transport errors',str(cr['http_503'])+' / '+str(cr['other_http_errors'])+' / '+str(cr['transport_errors'])],
            ['New primary observed',c['new_primary_observation']['timestamp']],
            ['Observed stop-to-primary-detection seconds',c['observed_election_seconds']],
            ['First successful write after errors',stamp(cw['first_success_after_errors'])],
            ['Observed stop-to-write-recovery seconds',cw['stop_to_recovery_seconds']],
            ['First-error-to-write-recovery seconds',cw['error_to_recovery_seconds']],
            ['Crashed node restart started',c['start']['start_utc']],
            ['Final roles',', '.join(x['name']+' '+x['state'] for x in c['final_members'])],
            ['Acknowledged control-record retention',c['retention']]]),
          'Sources: [crash write probe](logs/probe_primary_crash.txt), '
          '[crash read probe](logs/probe_primary_crash_reads.txt), '
          '[supplement events](logs/supplement-events.jsonl), '
          '[supplement result](logs/supplementary-results.json). '
          'The abrupt failure removes the opportunity for a graceful handoff and makes the '
          'observed client error interval distinct from the required Docker stop test.']
        insert=report.index('## 4. Conclusions & recommendations')
        report[insert:insert]=crash_section
    first=result['load'][0]; hundred=result['load'][-1]; last=all_load[-1]
    ratio=(last['rps']/hundred['rps'])/(last['users']/hundred['users'])
    report.append('At 10 users, throughput was {:.3f} RPS with p95 {:.0f} ms; at 100 users it was '
      '{:.3f} RPS with p95 {:.0f} ms. The highest tested level was {} users: {:.3f} RPS, '
      'p95 {:.0f} ms, failures {:.3f}%. Relative throughput per user versus the 100-user level '
      'was {:.1f}%.'.format(first['rps'],first['p95_ms'],hundred['rps'],hundred['p95_ms'],
       last['users'],last['rps'],last['p95_ms'],last['error_percent'],100*ratio))
    breached=next((x for x in all_load if not x['targets_pass']),None)
    if breached:
        report.append('The first explored R48 target breach occurred at {} users. This is an observed '
          'local operating limit for the selected workload, not an exact universal saturation '
          'capacity. A target can fail for one endpoint even if the aggregate passes. Its original '
          'per-endpoint numbers remain above; the target was not changed after testing.'.format(breached['users']))
    else:
        report.append('No R48 target breach was observed in the measured range. A hard saturation '
          'point was not established; the largest achieved RPS is a measured lower bound on '
          'capacity under this think-time workload, not a maximum-capacity claim.')
    eight=next((x for x in all_load if x['users']==800),None)
    report.append('At the 800-user level, '+str(eight['failures'] if eight else 0)+' failures were transport failures represented by '
      'Locust status 0 (no HTTP response), not an HTTP status code returned by the application. '
      'The original error labels were generic; the supplementary high-load run preserved '
      'underlying transport exceptions rather than replacing them with expected-status labels. '
      'See [transport diagnostics](logs/bottleneck-analysis.json).')
    diagnostics=json.loads((LOG/'bottleneck-analysis.json').read_text())
    report.append('**Evidence-supported limit:** '+diagnostics['cause_assessment']+' '
      'From 800 to 1600 users throughput changed by {:.2f}% despite doubling users; '
      'latency and transport failure rate increased. This establishes saturation/degradation of '
      'the tested end-to-end arrangement in that range, while a single server-side causal '
      'bottleneck is not proven. The generator approached one full CPU core in the resource '
      'samples, making an isolated generator/ingress comparison the first diagnostic priority.'.format(
        diagnostics['throughput_change_800_to_1600_percent']))
    report.append('The `_id` lookup already uses MongoDB\'s existing primary-key index. Record '
      'writes add database/majority work that /time does not perform; endpoint latency differences '
      'alone do not prove that MongoDB is the bottleneck. Compare the measured API, MongoDB, nginx '
      'and generator CPU columns. Shared VM/host limits and the fixed twelve API threads are '
      'plausible constraints; confirming a single causal bottleneck requires a controlled '
      'one-variable comparison. The sampled resource data bounds the conclusion rather than '
      'inventing an unsupported cause.')
    report += [
      '**Priority 1 - isolate the generator and modernize its Python runtime.** Run the same fixed '
      'workload from a separate machine or reserved CPU resources with supported Python/OpenSSL. '
      'This removes contention between the generator, Docker and desktop applications, and '
      'addresses the recorded Python 3.9/LibreSSL warnings (current traffic is local HTTP). '
      'Expected impact: a more reliable server-capacity estimate and less generator-induced '
      'latency; no improvement percentage is claimed without measurement.',
      '**Priority 2 - tune API concurrency within the measured memory/CPU budget.** Compare the '
      'current one-worker/four-thread API with one controlled alternative, for example two '
      'workers with bounded threads and pools, while keeping MongoDB concerns, request mix '
      'and nginx policy unchanged. Expected impact: less application queueing if the workers '
      'are the active constraint; extra processes can also raise memory/CPU pressure, so '
      'retain only a measured improvement. Do not weaken majority acknowledgement to make '
      'benchmark numbers look better.',
      '**Re-test after each change:** repeat the 10/50/100-user 60 s runs and the highest '
      'exploratory level with the same warm-up/ramp and multiple repetitions; compare both '
      'endpoint and aggregate p95, RPS, error rate, CPU and memory. Repeat TC14-TC17 to verify '
      'that performance tuning preserves 503 handling, balancing, automatic election and '
      'acknowledged-record retention.',
      '## 5. Reflection questions',
      '### 1. Why does MongoDB stop accepting writes when the primary fails, and what CAP choice is involved?',
      'Writes require an elected primary and majority acknowledgement in this configuration. '
      'The surviving two members elect a new primary; probes and the timeline above show what '
      'clients actually observed. Under a partition, a minority cannot confirm majority writes, '
      'prioritizing the configured consistency guarantees over minority write availability. '
      'A node-stop test illustrates recovery, while CAP specifically concerns partitions.',
      '### 2. How does reading from a primary differ from a secondary?',
      'This API chooses primary reads with majority read concern. Secondary reads can distribute '
      'read load and keep some reads available during a primary problem, but replication lag '
      'can return stale data. They are suitable for delay-tolerant analytics and less suitable '
      'for immediately confirming a user\'s update. Majority writes alone do not imply '
      'linearizable reads or eliminate all failover uncertainty.',
      '### 3. What does nginx do when one service copy stops?',
      'The api2-down distribution above excludes api2 and shows the remaining copies responding. '
      '`max_fails=1` counts a qualifying unsuccessful attempt during `fail_timeout=5s`; the node '
      'is temporarily unavailable for that period. `proxy_next_upstream error timeout http_502` '
      'allows an eligible request to try another upstream, with at most three tries. Requests '
      'already delivered cannot all be safely replayed; `non_idempotent` is not enabled. '
      'Docker DNS resolution lets a returning or recreated hostname be resolved again.',
      '### 4. Why must the service be stateless?',
      'nginx can send creation and reading to different API copies. TC12 confirms this with '
      'real requests. Shared records must live in MongoDB, not one API\'s memory/disk, so a '
      'stopped API does not own the only copy of data. In Lab 4, Redis required manual replica '
      'promotion, application redirection and reconciliation. Here MongoDB\'s voting replica '
      'set elects a new primary and PyMongo discovers it from the seed list without changing '
      'application source or manually promoting a node.',
      *screenshot_evidence(),
      '## Evidence and references',
      'The submitted screenshots are identified individually in [screenshots/README.md](screenshots/README.md). '
      'Archived-log browser captures are labelled as such and do not impersonate a live terminal. '
      'All underlying logs/CSVs accompany them. Final state is checked in '
      '[final-verification.json](logs/final-verification.json); file integrity is recorded in `MANIFEST.sha256`.',
      'Primary documentation: [MongoDB elections](https://www.mongodb.com/docs/manual/core/replica-set-elections/), '
      '[PyMongo timeout semantics](https://pymongo.readthedocs.io/en/4.10.1/examples/timeouts.html), '
      '[nginx retry conditions](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_next_upstream), '
      '[nginx DNS resolution](https://nginx.org/en/docs/http/ngx_http_upstream_module.html#resolve), '
      '[Locust 2.32.4](https://docs.locust.io/en/2.32.4/).']
    (ROOT/'test_report.md').write_text('\n\n'.join(report)+'\n')
    print('Generated measured report:',ROOT/'test_report.md')

if __name__=='__main__': main()
