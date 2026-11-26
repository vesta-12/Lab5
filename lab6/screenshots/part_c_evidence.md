# Part C — genuine GitHub Actions screenshots

The five JPEGs below were captured directly from the actual GitHub Actions
interface. No pixels, statuses or outputs were generated, reconstructed or
edited. They are browser captures, not native Terminal screenshots.
Public summary pages were viewed without browser login; authenticated GitHub
CLI/API access independently verified the jobs, downloaded artifacts and logs.
File hashes, source URLs and capture timestamps are recorded in
[ci_sources.json](ci_sources.json).

| Screenshot | Actual source | Evidence |
| --- | --- | --- |
| [06_ci_first_green.jpg](06_ci_first_green.jpg) | [GitHub page](https://github.com/vesta-12/Lab5/actions/runs/45892096178) | Initial GREEN workflow |
| [07_ci_intentional_red.jpg](07_ci_intentional_red.jpg) | [GitHub page](https://github.com/vesta-12/Lab5/actions/runs/45892227649) | Intentional RED workflow |
| [08_ci_package_skipped.jpg](08_ci_package_skipped.jpg) | [GitHub page](https://github.com/vesta-12/Lab5/actions/runs/45892227649/job/140157479825) | Package job skipped after test failure |
| [09_ci_restored_green.jpg](09_ci_restored_green.jpg) | [GitHub page](https://github.com/vesta-12/Lab5/actions/runs/45892413211) | Restored GREEN workflow |
| [10_ci_artifact.jpg](10_ci_artifact.jpg) | [GitHub page](https://github.com/vesta-12/Lab5/actions/runs/45892413211#artifacts) | Uploaded lambda-package artifact |

All required Part C captures are present; no manual CI screenshot is required.
For an optional larger reproduction, open the source URL in your browser and
capture the visible GitHub page. For full test output, sign in and open the
`test` job, then expand **Run all Lab 6 tests**. The RED log must show the
intentional AssertionError; the latest GREEN log must show **39 passed**.
For a manual artifact capture, open Run 3, scroll to **Artifacts**, and include
`lambda-package`, its size and digest. Do not substitute a different run.

The original Part B checklist and the user's existing `1.png`, `2.png`, `3.png`
remain unchanged. See [the CI evidence summary](../logs/part_c_ci_evidence.md)
for exact commit SHAs, raw job/API records and package-content checks.
