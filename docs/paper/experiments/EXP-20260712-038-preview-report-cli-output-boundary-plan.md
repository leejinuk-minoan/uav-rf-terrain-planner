# EXP-20260712-038 - Preview Report CLI Output Boundary Plan

## Experiment Purpose

Record the documentation-only boundary plan for connecting the implemented pure preview report formatter to report stdout and explicit report-file output in a later Local task.

## Input Data

Existing repository documentation, source, and tests only:

- current preview pipeline, CLI contract, artifact workflow, and reconciliation documents;
- Task 029A report formatter boundary plan;
- implemented `preview_cli.py`, `preview_appendix_table.py`, and `preview_report.py`;
- existing preview CLI, table, saved-input, artifact-workflow, and report formatter tests;
- Task 029B handoff and EXP-20260712-037;
- README, experiment index, and repository agent guidance.

No code execution, CLI execution, JSON read/write, table generation, report generation, report-file output, real raster, `METADATA_MAP` content, GIS file, QGIS project, generated output, or external dataset is used.

## Method

1. Confirm PR #75 and Task 029B are merged into `main`.
2. Confirm the current source and output selectors in `preview_cli.py`.
3. Confirm the pure formatter signature, exception, validation reuse, and terminal-newline behavior.
4. Define proposed `--report` and `--output-report PATH` selectors.
5. Define source/output compatibility for synthetic and saved JSON input.
6. Define stdout behavior without double newline.
7. Define explicit report-file behavior using the existing text writer and overwrite policy.
8. Define argument validation, including rejection of report output with `--max-records`.
9. Preserve status codes, MGRS boundaries, source-zone interpretation, and internal-coordinate exclusion.
10. Define Task 030B Local scope, tests, forbidden changes, and completion reporting.
11. Review the final GitHub diff for documentation-only scope.

## Expected Result

- One architecture plan fixes the report CLI boundary.
- One Local prompt narrows Task 030B to CLI integration and focused tests.
- One handoff records source/output, newline, file, status, coordinate, and artifact decisions.
- Existing formatter behavior remains unchanged.
- Existing JSON, text, table, and saved-input behavior remains unchanged.
- No source, tests, generated report, or data artifact is committed.

## Actual Result

Task 030A prepares:

```text
docs/architecture/preview-report-cli-output-boundary-plan.md
docs/prompts/local-task-030b-preview-report-cli-output.md
docs/handoff/task-030a-preview-report-cli-output-boundary-plan.md
docs/paper/experiments/EXP-20260712-038-preview-report-cli-output-boundary-plan.md
```

The proposed CLI surface is:

```text
--report
--output-report PATH
```

Both synthetic and saved preview JSON sources are planned to support report stdout and report-file output.

The formatter's existing one-trailing-newline contract is preserved. Report stdout is planned to use an `end=""` write so the CLI does not add a second newline. Report output combined with `--max-records` is planned as a status 2 argument error.

## Metrics

- Architecture plans added: 1
- Local implementation prompts added: 1
- Handoff documents added: 1
- Experiment records added: 1
- Proposed CLI selectors: 2
- Report-compatible source selectors: 2
- Existing output selectors preserved: 5
- Existing status meanings preserved: 4
- New source files changed: 0
- Test files changed: 0
- Formatter behavior changes: 0
- Preview schema changes: 0
- Generated runtime artifacts committed: 0
- Terrain or GIS files added: 0

## CI / Local Test Result

Local compileall, pytest, Ruff, mypy, CLI execution, JSON read/write, report generation, and report-file output are not run by the Cloud Agent for this documentation-only task.

GitHub Actions is checked after PR creation on the final documentation head and reported in the completion report. The workflow, runners, matrix, cache, and artifact policy are unchanged.

## Interpretation

The proposed boundary creates this controlled path:

```text
existing source selector
→ existing preview dictionary
→ existing pure report formatter
→ report stdout or explicit report file
```

Separating the CLI plan from implementation prevents report integration from silently changing formatter sections, saved-input rules, output conflicts, path protection, status codes, or artifact policy.

Rejecting `--max-records` with report output avoids an inconsistent report in which summary counts and the embedded appendix table could refer to different visible record sets.

## Limitations

This record does not implement or execute report CLI behavior. It does not inspect runtime report output, test write failures, assess actual MGRS geography, connect real terrain data, validate field RF conditions, or test Local environment behavior.

The planned newline decision depends on the currently implemented formatter returning exactly one terminal newline.

## Figure/Table Candidacy

The source/output compatibility matrix and the staged source-to-formatter-to-output flow are candidates for a future developer architecture table.

No rendered figure, screenshot, generated table artifact, report file, image, or PDF is created.

## Public Repository Sensitivity Check

Only repository Markdown documentation and an index update are included. No private path, account data, credential, terrain raster, GIS file, `METADATA_MAP` content, generated JSON/text/report artifact, QGIS project, CSV, PDF, image, archive, or external data is included.

The plan remains an offline research, education, simulation, and review workflow.

## Follow-Up Tasks

1. Task 030B-Local: implement report stdout and explicit report-file output using EXP-20260712-039.
2. Preserve Task 029B's pure formatter behavior and tests.
3. Reconcile implemented workflow documentation after Task 030B is merged.
4. Keep rendered UI and real-terrain integration as separate reviewed tasks.
