# EXP-20260712-029 - Preview Table Output Surface Plan

## Experiment Purpose

Record the documentation-only design of a minimal CLI stdout and explicit file-output surface for the existing preview appendix-table formatter.

## Input Data

Existing repository source files, tests, architecture documents, handoff records, experiment records, README content, and agent-operation guidance only.

No real raster, `METADATA_MAP` content, GIS file, map screenshot, CSV, image, PDF, generated preview, generated table, generated report, or QGIS project file is used.

## Method

Review the existing synthetic preview CLI, output contract, contract regression tests, appendix-table boundary, Task 024B formatter, formatter tests, handoff records, and experiment records.

Define candidate options, output-selector conflicts, explicit file rules, status-code mappings, MGRS and internal-coordinate boundaries, source-zone metadata handling, generated-artifact policy, and a narrow Task 025B Local implementation scope.

## Expected Result

- One architecture document defines the table output surface.
- Existing CLI commands and behavior remain unchanged.
- `--table` is documented as the candidate table stdout selector.
- `--output-table PATH` is documented as the candidate explicit table-file selector.
- Five output selectors are governed by one mutual-exclusion policy.
- Existing explicit file and overwrite rules are reused.
- Existing status codes 0, 1, 2, and 3 retain their meanings.
- `candidate_cell_mgrs` and MGRS remain the table coordinate contract.
- Internal/debug coordinate fields remain excluded.
- Source-zone fields remain interpretation metadata.
- One focused Task 025B-Local prompt is added.
- No source or test code is changed.

## Actual Result

Implemented on the Task 025A documentation branch. The architecture plan, Task 025B-Local prompt, handoff record, experiment record, README summary, and experiment index update were prepared without changing source or test code.

The plan proposes two minimal output options while preserving default plain-text preview, JSON stdout, JSON file, plain-text file, formatter, terrain, scoring, route, waypoint, report, and UI behavior.

## Metrics

- Architecture documents added: 1
- Local implementation prompts added: 1
- Handoff documents added: 1
- Experiment records added: 1
- Candidate CLI options documented: 2
- Output selectors governed: 5
- Status codes preserved: 4
- Existing CLI commands changed: 0
- Source files changed: 0
- Test files changed: 0
- JSON fields changed: 0
- Formatter fields or columns changed: 0
- Generated output files added: 0
- Terrain or GIS files added: 0

## CI / Local Test Result

Local compile, pytest, Ruff, mypy, formatter execution, CLI execution, and file generation were not run by the Cloud Agent. GitHub Actions is checked after pull request creation and rechecked on the final documentation head before completion reporting.

## Interpretation

The existing formatter can be exposed later without introducing a new data contract. A single output-selector policy and reuse of the current text writer prevent table output from diverging from established parser, path, overwrite, encoding, newline, status-code, and cleanup behavior.

## Limitations

This task does not implement or execute the proposed options, change source or tests, change formatter behavior, generate a file, access terrain data, convert MGRS, assess coordinate accuracy, recalculate scores, or render report, UI, map, or HTML content.

## Figure/Table Candidacy

The current-output-mode table, proposed-selector policy, status-code table, and Task 025B acceptance criteria are candidates for adaptation into an implementation or methodology appendix.

No rendered figure, screenshot, generated table artifact, image, or PDF is created.

## Public Repository Sensitivity Check

Only repository Markdown documentation and index updates are included. No private absolute path, sensitive coordinate, credential, token, secret, local dataset, terrain raster, GIS file, generated preview, generated table, generated report, CSV, PDF, image, QGIS project, or archive is included.

## Follow-Up Tasks

1. Task 025B-Local: connect the existing formatter to `--table` and `--output-table PATH`.
2. A later task may add JSON-file input only after a separate input-policy review.
3. A separate report task may consume the table string.
4. A separate UI task may consume the preview dictionary or records.
5. Real-terrain integration remains outside this synthetic output-surface plan.
