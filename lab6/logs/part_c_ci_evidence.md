# Part C — verified GitHub Actions evidence

All observations below come from completed push-triggered GitHub runs, retrieved
with the authenticated GitHub CLI/API. They are not inferred from local tests.
Original `run.json`, `jobs.json`, `artifacts.json` and full `github-actions.log`
files are retained under `ci/<label>/`. `verified.json` records actual download
and source-content checks. All three original commits remain in Git history.

| Push run | Commit | Actual tests | test | package | Artifacts | GitHub run |
| --- | --- | --- | --- | --- | --- | --- |
| 1 — GREEN | [8b6a176](https://github.com/vesta-12/Lab5/commit/8b6a176913980a6845d1fd6b67fa1de534e0cba2) | 39 passed | success | success | 1 | [Run 45892096178](https://github.com/vesta-12/Lab5/actions/runs/45892096178) |
| 2 — RED | [ebab758](https://github.com/vesta-12/Lab5/commit/ebab758d03f9fcbeb24080f4dbe1f5c928b680a6) | 39 passed, 1 intentional failure | failure | skipped | 0 | [Run 45892227649](https://github.com/vesta-12/Lab5/actions/runs/45892227649) |
| 3 — GREEN | [e96b2a3](https://github.com/vesta-12/Lab5/commit/e96b2a3e97b020593ce85cf5cc560e02cf6acaca) | 39 passed | success | success | 1 | [Run 45892413211](https://github.com/vesta-12/Lab5/actions/runs/45892413211) |

## green-1

Run: [45892096178](https://github.com/vesta-12/Lab5/actions/runs/45892096178)  
Commit: `8b6a176913980a6845d1fd6b67fa1de534e0cba2`  
Event: `push`; conclusion: `success`.

[Run API](ci/green-1/run.json), [jobs API](ci/green-1/jobs.json), [artifacts API](ci/green-1/artifacts.json), [original log](ci/green-1/github-actions.log), [verification](ci/green-1/verified.json).

- [test](https://github.com/vesta-12/Lab5/actions/runs/45892096178/job/140156981022): **success**.
- [package](https://github.com/vesta-12/Lab5/actions/runs/45892096178/job/140157115963): **success**.

- Uploaded artifact: [lambda-package (ID 15152660380)](https://github.com/vesta-12/Lab5/actions/runs/45892096178/artifacts/15152660380); 1243 bytes; expired: `False`.
- GitHub artifact-bundle digest: `sha256:6f7a27faa090009bd696f0afcca540a11800d9a3108b5bf78fbe3e2353de3a94`.
- Downloaded inner ZIP SHA-256: `78717f4e52dff3ac840288fc1cdeb9bb0764cf35f73d2cded28f0e011424d142`.
- ZIP members: `['lambda_function.py']`; CRC check passed.
- Extracted source SHA-256: `2df881141409b1eba3d954ea9670070a7c4cab1711fa8f6cc33187fe787fe961`; matches this commit's handler byte-for-byte.

## red

Run: [45892227649](https://github.com/vesta-12/Lab5/actions/runs/45892227649)  
Commit: `ebab758d03f9fcbeb24080f4dbe1f5c928b680a6`  
Event: `push`; conclusion: `failure`.

[Run API](ci/red/run.json), [jobs API](ci/red/jobs.json), [artifacts API](ci/red/artifacts.json), [original log](ci/red/github-actions.log), [verification](ci/red/verified.json).

- [test](https://github.com/vesta-12/Lab5/actions/runs/45892227649/job/140157405555): **failure**.
- [package](https://github.com/vesta-12/Lab5/actions/runs/45892227649/job/140157479825): **skipped**.

The original pytest log reports **1 failed, 39 passed** and the intentional
AssertionError. The package job is skipped and the API artifact list is empty
(`total_count: 0`). No infrastructure failure caused this RED result.

## green-2

Run: [45892413211](https://github.com/vesta-12/Lab5/actions/runs/45892413211)  
Commit: `e96b2a3e97b020593ce85cf5cc560e02cf6acaca`  
Event: `push`; conclusion: `success`.

[Run API](ci/green-2/run.json), [jobs API](ci/green-2/jobs.json), [artifacts API](ci/green-2/artifacts.json), [original log](ci/green-2/github-actions.log), [verification](ci/green-2/verified.json).

- [test](https://github.com/vesta-12/Lab5/actions/runs/45892413211/job/140158019215): **success**.
- [package](https://github.com/vesta-12/Lab5/actions/runs/45892413211/job/140158080264): **success**.

- Uploaded artifact: [lambda-package (ID 15151678519)](https://github.com/vesta-12/Lab5/actions/runs/45892413211/artifacts/15151678519); 1243 bytes; expired: `False`.
- GitHub artifact-bundle digest: `sha256:c1f42af126a2c9519b2acbc97297d1ed27d1c79a4015d3b6ffbf6e44372225c4`.
- Downloaded inner ZIP SHA-256: `acdfac26e0eed72bd7d374e3a240e74a6077fe2320b24382f7f68ab105d0e2bf`.
- ZIP members: `['lambda_function.py']`; CRC check passed.
- Extracted source SHA-256: `2df881141409b1eba3d954ea9670070a7c4cab1711fa8f6cc33187fe787fe961`; matches this commit's handler byte-for-byte.

## Local regression check and screenshots

After the restored GREEN, the unchanged local Part A/Part B suite passed **39 tests**
on Python 3.12.16 with pytest 8.3.5. Original output:
[part_c_local_pytest.log](part_c_local_pytest.log) and
[part_c_local_pytest.xml](part_c_local_pytest.xml).

[Five genuine GitHub browser captures](../screenshots/part_c_evidence.md) show
initial success, intentional failure, skipped packaging, restored success and
the uploaded artifact. They depict the actual GitHub interface, not reconstructed
terminal output. Native Part B images added by the user are retained unchanged.

Saving these evidence files requires a later documentation-only commit; the
workflow also runs on that push. That additional run does not replace any of the
three required runs above. Its final status is verified separately on GitHub.
