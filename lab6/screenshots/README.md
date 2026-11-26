# Lab 6 screenshot evidence

All required Part B and Part C subjects are present. The three user-provided
Part B PNGs contain combined views covering five requirements; their original
filenames and pixels are preserved. Five Part C JPEGs are actual GitHub browser
captures, indexed with URLs and hashes in [part_c_evidence.md](part_c_evidence.md)
and [ci_sources.json](ci_sources.json). No images were generated or reconstructed
from logs.

## Part B - actual local HTTP demonstration

| Required evidence | Existing image | Visible observation |
| --- | --- | --- |
| GET /time - 200 | [1.png](1.png) | HTTP 200, UTC time, server_time and served_by. |
| POST /echo - 200 | [1.png](1.png) | HTTP 200 and matching reply/message for Hello from Lab 6. |
| Invalid request - 400 | [2.png](2.png) | HTTP 400 and the missing-message JSON error. |
| Unknown route - 404 | [2.png](2.png) | HTTP 404 and the route-not-found JSON error. |
| Local Runner and request log | [3.png](3.png) | Python 3.12.16, listening URL, all four request/status log entries. |

The `zsh: command not found: #` messages in 1.png and 2.png came from pasted
comment lines in an interactive shell. They are not Lambda or HTTP failures:
the genuine HTTP responses and the corresponding server log are visible.
The images remain unedited. The reproducible demonstration commands in the
main README do not require pasting comments.

Original machine-readable curl evidence is in
[part_b_http_checks.log](../logs/part_b_http_checks.log); automated HTTP tests
also verify Unicode, malformed JSON, routing and body handling.

## Part C - actual GitHub Actions UI

| Required evidence | Existing image |
| --- | --- |
| First GREEN | [06_ci_first_green.jpg](06_ci_first_green.jpg) |
| Intentional RED | [07_ci_intentional_red.jpg](07_ci_intentional_red.jpg) |
| Package job skipped | [08_ci_package_skipped.jpg](08_ci_package_skipped.jpg) |
| Restored GREEN | [09_ci_restored_green.jpg](09_ci_restored_green.jpg) |
| Uploaded lambda-package | [10_ci_artifact.jpg](10_ci_artifact.jpg) |

These are historical captures of the original push runs, not screenshots of
the later workflow-path rename. Their original run URLs remain available.
Authenticated GitHub API records and the complete job logs are retained in
[the CI evidence summary](../logs/part_c_ci_evidence.md).

No additional manual screenshot is required for the supplied criteria.
Optional higher-resolution replacements can be captured from the same source
pages, but existing images must not be represented as a new execution.
