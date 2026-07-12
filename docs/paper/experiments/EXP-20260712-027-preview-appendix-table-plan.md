# EXP-20260712-027 - Preview Appendix Table Boundary Plan

## Experiment Purpose

Record the documentation-only definition of a consumer boundary for transforming the reviewed preview JSON dictionary into a paper appendix table or developer review table before formatter implementation begins.

## Input Data

Existing repository source files, tests, architecture documents, handoff records, experiment records, README content, and agent-operation guidance only.

No real raster, `METADATA_MAP` content, GIS file, map screenshot, CSV file, image, PDF, generated preview, generated table, generated report, or QGIS project file is used.

## Method

Review the Tasks 021G through 023B preview pipeline, CLI output contract, CLI implementation, focused contract tests, handoff records, and experiment records. Extract the validated JSON top-level and record fields, MGRS boundary, internal/debug exclusions, source-zone interpretation fields, and existing file policy. Define a non-breaking table-consumer boundary and a focused Task 024B-Local prompt.

## Expected Result

- One architecture document defines the preview appendix-table boundary.
- The reviewed preview JSON dictionary or JSON file is the input contract.
- Four intended consumers are compared.
- Eleven default table columns are documented.
- `row_no` is defined as a one-based display value rather than a JSON field or rank.
- JSON record order is preserved by default.
- Existing score values are displayed without recalculation.
- `candidate_cell_mgrs` and `MGRS` remain the user-facing coordinate contract.
- Internal/debug coordinate fields remain excluded.
- Source-zone values remain interpretation metadata.
- One focused Task 024B-Local formatter prompt is added.
- No source or test code is changed.

## Actual Result

Implemented in PR #65. The architecture plan, Task 024B-Local prompt, handoff record, experiment record, README summary, and experiment index entry were added without changing source or test code.

The plan separates a pure Python string formatter from existing CLI, file-output, report, UI, terrain, scoring, route, and waypoint behavior. It also preserves the validated Tasks 023A/023B JSON contract as an immutable input boundary for the next task.

## Metrics

- Architecture documents added: 1
- Local implementation prompts added: 1
- Handoff documents added: 1
- Experiment records added: 1
- Intended consumer categories documented: 4
- Preview JSON top-level fields preserved: 8
- Preview JSON record fields preserved: 13
- Recommended table columns documented: 11
- Derived display-only fields documented: 1 (`row_no`)
- Source files changed: 0
- Test files changed: 0
- CLI options added: 0
- JSON fields changed: 0
- Generated output files added: 0
- Local terrain data files added: 0
- GIS files added: 0

## CI / Local Test Result

Local commands were not run by the Cloud Agent. GitHub Actions CI completed successfully for the initial PR #65 documentation head. CI is rechecked on the final experiment-status head before completion reporting.

## Interpretation

The reviewed preview JSON output can now support a later appendix-table formatter without coupling that formatter to the CLI or changing the established preview schema. Preserved order and display-only row numbering prevent the table layer from silently introducing ranking or rescoring behavior.

## Limitations

This task does not execute or implement a formatter, create table files, change source or tests, add CLI options, change preview fields, generate reports, render UI or HTML surfaces, access terrain data, convert MGRS coordinates, or change scoring, LOS/Fresnel, route, or waypoint logic.

## Figure/Table Candidacy

The intended-consumer matrix, recommended-column table, column-interpretation table, and Task 024B acceptance criteria are candidates for adaptation into a methodology or implementation appendix.

No rendered figure, image, SVG, PDF, or generated table artifact is created.

## Public Repository Sensitivity Check

Only repository Markdown documentation and index updates are included. No private absolute path, sensitive coordinate, credential, token, secret, local dataset, GIS file, generated preview, generated table, generated report, CSV, PDF, image, QGIS project, or archive is included.

## Follow-Up Tasks

1. Task 024B-Local: add a pure Python preview appendix table formatter and focused tests.
2. A separate file-output task may later persist reviewed table strings.
3. A separate report task may incorporate a reviewed table into a paper appendix.
4. A separate UI task may consume the existing JSON-ready record list.
5. Real-terrain integration remains outside the synthetic preview-consumer contract.
