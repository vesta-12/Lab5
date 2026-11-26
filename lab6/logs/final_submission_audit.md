# Lab 6 - final submission criteria audit

Student: Sofiya Serbina. Group: ICT4401-ENG-1.

This audit covers the supplied 25-point criteria. It records evidence of
completion, not an instructor-awarded grade. Original measurements and the
intentional RED commit are preserved; no failure scenario was repeated.

| Criterion | Available points | Status | Confirmed evidence |
| --- | --- | --- | --- |
| Part A - function and tests | 8 | DONE | [Handler](../lambda_function.py); [19 direct cases](../tests/test_handler.py); GET /time, POST /echo, JSON 200/400/404, negative and edge inputs. |
| Part B - local B-2 execution | 6 | DONE | [Runner](../local_runner.py); [20 real HTTP/TCP cases](../tests/test_local_runner.py); [curl log](part_b_http_checks.log); [three original PNGs covering all five subjects](../screenshots/README.md). |
| Part C - GitHub Actions | 8 | DONE | [Single current ci.yml](../../.github/workflows/ci.yml), Python 3.12, push trigger, test/package jobs, needs: test; [actual GREEN / RED / GREEN](part_c_ci_evidence.md), skipped package and zero artifacts on RED, downloaded valid packages on GREEN. |
| Report and reproducibility | 3 | DONE | [Report](../report.pdf): two A4 pages, all four reflection answers, real run/evidence links, no claimed AWS cold-start measurement; [README](../README.md), genuine screenshots and original job logs. |

## Evidence checks

- The original local suite passed **39/39** on Python 3.12.16, and the successful
  GitHub runs passed the same 39 cases. The temporary RED run had exactly one
  intentional assertion failure plus 39 passes.
- Original cycle: [GREEN 1](https://github.com/vesta-12/Lab5/actions/runs/45892096178),
  [RED](https://github.com/vesta-12/Lab5/actions/runs/45892227649),
  [GREEN 2](https://github.com/vesta-12/Lab5/actions/runs/45892413211).
  [The subsequent evidence commit also passed](https://github.com/vesta-12/Lab5/actions/runs/45892835404).
- The renamed workflow is byte-for-byte identical to the previous lab6-ci.yml;
  only its path changes. There is one workflow file, not two parallel pipelines.
  Historical run records retain their original paths and are not rewritten.
- Download checks establish that `lambda_function.zip` contains exactly
  `lambda_function.py` at the root, with bytes matching the tested commit.
- Workflow permissions are `contents: read`; checkout does not persist
  credentials. No AWS access key, repository secret or AWS deployment was added.
- PDF pages were rendered and visually inspected for readable text, complete
  tables and absence of clipping. Links and page count were checked separately.
- Existing Part A/B code, tests, saved results and user screenshots are preserved.
  Earlier laboratory files and user IDE files are unchanged.
- All five Part B screenshot subjects and all five Part C subjects are present.
  No missing capture or fabricated image has been substituted.

## Publication check

The final documentation commit triggers the same tests and packaging through
the renamed workflow. The live result is available in
[current ci.yml runs for this branch](https://github.com/vesta-12/Lab5/actions/workflows/ci.yml?query=branch%3Alab6-serverless-ci).
Inspect its commit SHA, successful test/package jobs and `lambda-package` under
Artifacts. The final publication is independently verified through GitHub API
and artifact download; a local pytest result is not used as its substitute.

Submit the [Lab 6 GitHub folder](https://github.com/vesta-12/Lab5/tree/lab6-serverless-ci/lab6)
or branch link. No separate laboratory submission ZIP is required or generated.
The CI-produced Lambda build artifact remains required and available on GitHub.
