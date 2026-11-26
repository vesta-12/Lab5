# Part B screenshot checklist

No screenshots have been fabricated or rendered from logs. Native Terminal
automation is unavailable in the agent session: the computer-use tool refused
access to `com.apple.Terminal`. The five PNG files below therefore require
manual capture. The original actual HTTP responses are separately retained in
`../logs/part_b_http_checks.log`.

## Prepare two terminals

In the first Terminal or PyCharm terminal:

```bash
cd ~/Lab3_Docker_Kubernetes_Lab4
git branch --show-current
# Expected branch: lab6-serverless-ci
lab6/.venv/bin/python --version
lab6/.venv/bin/python lab6/local_runner.py
```

Keep this server running. Its startup output must show
`http://127.0.0.1:8000`. If this is already the Lab 6 runner, use the existing
server. If another application owns 8000, choose a free `LAB6_PORT` and replace
8000 in every command below; do not kill another application's process.

In the second terminal, run each command and capture its **new actual output**.
On macOS use Command+Shift+4, then Space, to capture the terminal window.
Make the command, HTTP status, Content-Type and complete JSON body readable.
Save each PNG under `lab6/screenshots/` with the exact filename below.

| Filename | Command / required content |
| --- | --- |
| `01_time_200.png` | `curl -i http://127.0.0.1:8000/time` — HTTP 200, current UTC `time`, matching `server_time` and `served_by`. |
| `02_echo_200.png` | `curl -i -H 'Content-Type: application/json' --data-binary '{"message":"Hello from Lab 6"}' http://127.0.0.1:8000/echo` — HTTP 200 with matching `reply` and `message`. |
| `03_invalid_400.png` | `curl -i -H 'Content-Type: application/json' --data-binary '{}' http://127.0.0.1:8000/echo` — HTTP 400 and JSON error. |
| `04_unknown_404.png` | `curl -i http://127.0.0.1:8000/unknown` — HTTP 404 and JSON error. |
| `05_local_runner.png` | First terminal: server launch command, listening URL and request log lines from the four curl commands. Capture while the server is still running. |

Additional optional evidence for malformed JSON and Unicode:

```bash
curl -i -H 'Content-Type: application/json' \
  --data-binary '{"message":' http://127.0.0.1:8000/echo
curl -i -H 'Content-Type: application/json' \
  --data-binary '{"message":"Hello, Привет, 世界 👋"}' http://127.0.0.1:8000/echo
```

These should produce HTTP 400 and HTTP 200 respectively. Escaped Unicode in
JSON is valid; the automated HTTP test verifies the decoded original string.
After capturing all five images, stop your server with Ctrl+C in its terminal.
Do not label archived log displays as live Terminal captures.
