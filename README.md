# Distributed & Cloud Computing - Laboratory Work 6

Student: **Sofiya Serbina**. Group: **ICT4401-ENG-1**.

The Lab 6 submission is on the **lab6-serverless-ci** branch.
Submit the GitHub branch link; no separate laboratory submission ZIP is required.

- [Lab 6 overview, setup, testing and demonstration](lab6/README.md)
- [Two-page report](lab6/report.pdf)
- [Genuine HTTP and GitHub Actions screenshots](lab6/screenshots/README.md)
- [GREEN / RED / GREEN evidence and original logs](lab6/logs/part_c_ci_evidence.md)
- [Final criteria audit](lab6/logs/final_submission_audit.md)
- [Current workflow](.github/workflows/ci.yml)
- [Latest branch CI runs and lambda-package artifacts](https://github.com/vesta-12/Lab5/actions/workflows/ci.yml?query=branch%3Alab6-serverless-ci)

The workflow runs Python 3.12 tests before creating the required `lambda-package`
build artifact. The selected B-2 option runs the function through a local HTTP
adapter without AWS deployment or stored AWS access keys.

Earlier laboratories, their reports, configurations and experiment evidence
remain in their existing folders and branches.
