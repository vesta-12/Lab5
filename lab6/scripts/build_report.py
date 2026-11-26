"""Build the two-page report from verified Lab 6 results, without rerunning tests."""

import argparse
from pathlib import Path

import reportlab
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, PageBreak


BASE = "https://github.com/vesta-12/Lab5"
BRANCH = BASE + "/tree/lab6-serverless-ci"
RUNS = [
    ("GREEN 1", "45892096178", "8b6a176", "39 passed", "test / package: success; 1 artifact"),
    ("RED", "45892227649", "ebab758", "39 passed, 1 failed", "test: failure; package: skipped; 0 artifacts"),
    ("GREEN 2", "45892413211", "e96b2a3", "39 passed", "test / package: success; 1 artifact"),
    ("Docs GREEN", "45892835404", "d8982bf", "39 passed", "test / package: success; 1 artifact"),
]
NAVY = colors.HexColor("#17364D")
GRAY = colors.HexColor("#52616B")
mac_fonts = Path("/System/Library/Fonts/Supplemental")
if (mac_fonts / "Times New Roman.ttf").exists():
    font_root = mac_fonts
    font_files = ["Times New Roman.ttf", "Times New Roman Bold.ttf",
                  "Times New Roman Italic.ttf", "Times New Roman Bold Italic.ttf"]
else:
    font_root = Path(reportlab.__file__).parent / "fonts"
    font_files = ["Vera.ttf", "VeraBd.ttf", "VeraIt.ttf", "VeraBI.ttf"]
for name, filename in zip(["Body", "BodyBold", "BodyItalic", "BodyBoldItalic"], font_files):
    pdfmetrics.registerFont(TTFont(name, str(font_root / filename)))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="BodyBold",
                             italic="BodyItalic", boldItalic="BodyBoldItalic")
BODY = ParagraphStyle("body", fontName="Body", fontSize=10.8, leading=14.2, spaceAfter=7)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=9, leading=11.7, spaceAfter=5)
CELL = ParagraphStyle("cell", parent=SMALL, fontSize=9.2, leading=11.8, spaceAfter=0)
HEADING = ParagraphStyle("heading", parent=BODY, fontName="BodyBold", fontSize=12.2,
                         leading=15, textColor=NAVY, spaceBefore=9, spaceAfter=6)
QUESTION = ParagraphStyle("question", parent=BODY, fontName="BodyBold", fontSize=11,
                          leading=14.1, textColor=NAVY, spaceBefore=8, spaceAfter=4)
TITLE = ParagraphStyle("title", fontName="BodyBold", fontSize=18.5, leading=22,
                       alignment=TA_CENTER, textColor=NAVY, spaceAfter=12)


def p(text, style=BODY):
    return Paragraph(text, style)


def link(url, label):
    return f'<link href="{url}" color="#145A80"><u>{label}</u></link>'


def page_frame(canvas, doc):
    width, height = A4
    canvas.saveState()
    canvas.setStrokeColor(NAVY)
    canvas.setLineWidth(0.6)
    canvas.line(50, height - 35, width - 50, height - 35)
    canvas.setFont("Body", 8.5)
    canvas.setFillColor(GRAY)
    canvas.drawString(50, 30, "Sofiya Serbina | ICT4401-ENG-1 | Distributed & Cloud Computing")
    canvas.drawRightString(width - 50, 30, f"{doc.page} / 2")
    canvas.restoreState()


def build(output):
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output), pagesize=A4, leftMargin=50, rightMargin=50,
                            topMargin=48, bottomMargin=47,
                            title="Laboratory Work 6 — A Serverless Function and CI/CD",
                            author="Sofiya Serbina", subject="Verified local function and GitHub CI evidence")
    story = [
        p("Laboratory Work 6 —<br/>A Serverless Function and CI/CD", TITLE),
        p("<b>Student:</b> Sofiya Serbina &nbsp;&nbsp; <b>Group:</b> ICT4401-ENG-1<br/>"
          "<b>Course:</b> Distributed &amp; Cloud Computing<br/>"
          "<b>Execution option:</b> B-2, Local Run without AWS &nbsp;&nbsp; <b>Date:</b> 27 November 2026"),
        p("1. Implementation Summary", HEADING),
        p("The Python 3.12 <b>lambda_handler(event, context)</b> processes HTTP API Gateway v2 "
          "events. GET /time returns UTC time; POST /echo validates a JSON object containing "
          "message. Compatibility is additive: time equals server_time, reply equals message, "
          "and served_by remains available. The function is stateless and uses no Flask, AWS "
          "SDK, database or local file storage."),
        p("The standard-library <b>Local Runner</b> binds 127.0.0.1:8000 (LAB6_PORT is configurable). "
          "It separates the URL path and query, reads the HTTP body, creates an event and calls "
          "the existing handler once. This is local HTTP emulation, not an AWS deployment."),
        p("GitHub Actions uses two jobs: <b>test</b> runs the complete pytest suite, then "
          "<b>package</b> runs only through needs: test. It creates lambda_function.zip with "
          "lambda_function.py at the archive root and uploads <b>lambda-package</b>. The final "
          "workflow path is .github/workflows/ci.yml; the historical runs below used lab6-ci.yml. "
          "Only contents: read is granted; no AWS credentials are needed."),
        p("2. Verification Results", HEADING),
        p("<b>39 passed</b>: 19 direct handler cases plus 20 real HTTP/TCP integration cases, "
          "verified locally on Python 3.12.16 and in GitHub Actions. Ten original curl checks "
          "confirm <b>200</b> for /time and /echo, <b>400</b> for missing message or malformed JSON, "
          "and <b>404</b> for an unknown route. Unicode, query routing and port configuration "
          "also passed; original responses and test logs are retained."),
    ]
    rows = [[p("<b>Push run</b>", CELL), p("<b>Commit</b>", CELL),
             p("<b>Actual pytest result</b>", CELL), p("<b>Jobs / artifact</b>", CELL)]]
    for label, run_id, sha, result, jobs in RUNS:
        rows.append([p(label + "<br/>" + link(BASE + "/actions/runs/" + run_id, run_id), CELL),
                     p(sha, CELL), p(result, CELL), p(jobs, CELL)])
    table = Table(rows, colWidths=[99, 60, 119, 217], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF0F4")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, NAVY),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor("#CDD6DC")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [table, Spacer(1, 7),
        p("RED was caused by an explicitly intentional AssertionError, not infrastructure. "
          "The temporary test was removed in the next commit; the failed commit remains in "
          "history. Successful-run artifacts were downloaded and checked for ZIP integrity, "
          "root layout and byte-for-byte equality with the committed handler.", SMALL),
        PageBreak(), p("3. Reflection Questions", HEADING),
        p("1. What is a cold start and when does it get in the way?", QUESTION),
        p("A cold start adds initialization of a new execution environment, runtime and "
          "function code before an invocation can be served. It matters for latency-sensitive "
          "APIs, especially after idle periods or during scale-out. This work used B-2: "
          "<b>no real AWS cold-start duration was measured</b>. See AWS documentation [1]."),
        p("2. When is a serverless function better, and when is a service in a container?", QUESTION),
        p("A small stateless, event-driven task with intermittent or bursty traffic fits a "
          "function; /time and /echo demonstrate this shape. A containerized service fits "
          "continuous processes, custom system dependencies or workloads requiring more "
          "runtime and resource control. Persistent data still belongs in external storage; "
          "the function's execution environment is not a durable data store."),
        p("3. Why does the pipeline run tests before packaging the artifact?", QUESTION),
        p("Packaging should publish code that has passed its checks. The dependency "
          "needs: test enforces that order: our RED run had 39 passes and one intentional "
          "failure, so package was skipped and no artifact was produced. Restoring the "
          "39 passing cases allowed lambda-package to be created again."),
        p("4. Why must access keys not be stored in code or the pipeline file, and where should they be stored?", QUESTION),
        p("Source and workflow files are copied and retained in Git history, so embedded "
          "keys can expose an account even after a later deletion. Prefer short-lived IAM "
          "role credentials: an execution role for Lambda and GitHub OIDC for cloud CI [2]. "
          "If a stored secret is unavoidable, use restricted GitHub environment/repository "
          "secrets or AWS Secrets Manager, not source code. B-2 requires no AWS access keys."),
        p("4. Evidence and Submission", HEADING),
        p("The report and all evidence are submitted through " + link(BRANCH + "/lab6", "the Lab 6 GitHub folder") +
          ". No separate laboratory submission ZIP is needed. The CI-generated Lambda ZIP "
          "remains the required build artifact. The existing GREEN / RED / GREEN cycle "
          "can be demonstrated directly from the run links on page 1.", SMALL),
        p(link(BASE + "/blob/lab6-serverless-ci/lab6/logs/part_c_ci_evidence.md", "CI evidence and original job/API records") +
          " &nbsp;|&nbsp; " + link(BASE + "/blob/lab6-serverless-ci/lab6/logs/part_b_http_checks.log", "Original curl output") +
          "<br/>" + link(BRANCH + "/lab6/screenshots", "Real HTTP and GitHub UI screenshots") +
          " &nbsp;|&nbsp; " + link(BASE + "/blob/lab6-serverless-ci/.github/workflows/ci.yml", "Current workflow") +
          " &nbsp;|&nbsp; " + link(BASE + "/actions?query=branch%3Alab6-serverless-ci", "Latest branch CI"), SMALL),
        p("Technical references", HEADING),
        p("[1] " + link("https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html", "AWS Lambda: execution environment lifecycle and cold starts") +
          "<br/>[2] " + link("https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws", "GitHub Docs: configuring OpenID Connect in AWS"), SMALL),
    ]
    doc.build(story, onFirstPage=page_frame, onLaterPages=page_frame)
    if doc.page != 2:
        raise ValueError(f"Expected a two-page report; generated {doc.page} pages")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "report.pdf")
    args = parser.parse_args()
    print(build(args.output))
