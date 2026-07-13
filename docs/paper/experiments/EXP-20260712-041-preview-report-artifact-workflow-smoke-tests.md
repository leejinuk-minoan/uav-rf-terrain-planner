# EXP-20260712-041 - Preview Report Artifact Workflow Smoke Tests

## Experiment Purpose
Verify documented report artifact workflows.
## Input Data
Synthetic preview and temporary saved JSON under `tmp_path`.
## Method
Exercise stdout/file, saved reuse, overwrite, force, limit rejection, and invalid input.
## Expected Result
Documented statuses and deterministic report content.
## Actual Result
Recorded in the Task 031B PR.
## Metrics
Four report workflows plus error-policy coverage.
## CI / Local Test Result
Local and CI results are recorded in the PR.
## Interpretation
Regression coverage only.
## Limitations
No real terrain or RF validation.
## Figure/Table Candidacy
None.
## Public Repository Sensitivity Check
No generated artifact committed.
## Follow-Up Tasks
Review future consumers separately.
