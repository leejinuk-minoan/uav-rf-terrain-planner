# EXP-20260712-025 - Preview CLI Output Contract

## Experiment Purpose

Record the documentation-only consolidation of the current synthetic preview CLI contract across stdout, explicit files, JSON fields, plain-text structure, status codes, MGRS fields, and file-output policy.

## Input Data

Existing repository source files, tests, architecture documents, handoff records, experiment records, README content, and agent-operation guidance only.

No real raster, `METADATA_MAP` content, GIS file, map screenshot, CSV file, image, PDF, generated preview, or QGIS project file is used.

## Method

Review `preview_cli.py`, the candidate preview and display helpers, the synthetic smoke, current CLI tests, and Tasks 022B/022C records. Extract the actual output modes, JSON fields, plain-text projection, status codes, MGRS boundary, internal-coordinate exclusions, and explicit file rules. Record a focused Task 023B-Local prompt for regression testing without feature changes.

## Expected Result

- One architecture document records the current CLI contract.
- Four output modes are compared.
- JSON stdout and JSON file share one semantic dictionary contract.
- Plain-text stdout and file share the existing human-readable projection.
- Status codes 0, 1, 2, and 3 are documented.
- Explicit path and overwrite rules are documented.
- `candidate_cell_mgrs` and `MGRS` remain the user-facing coordinate contract.
- Internal/debug coordinate fields remain excluded.
- Source-zone interpretation metadata remains separate from scoring.
- One focused Task 023B-Local prompt is added.
- No source or test code is changed.

## Actual Result

Implemented on the Task 023A branch. The architecture contract, Task 023B-Local prompt, handoff record, experiment record, README summary, and experiment index entry were added. Pull request and CI status are finalized after PR creation.

The review also records an important current behavior: JSON records include `source_zone`, `source_sensitive`, and `source_zone_reason`, while plain-text rows include `source_zone` and the header provides only an aggregate source-sensitive count. The documentation does not invent per-record plain-text fields that are absent from the implementation.

## Metrics

- Architecture documents added: 1
- Local implementation prompts added: 1
- Handoff documents added: 1
- Experiment records added: 1
- Output modes documented: 4
- Status codes documented: 4
- JSON top-level fields documented: 8
- JSON record fields documented: 13
- Source files changed: 0
- Test files changed: 0
- CLI options added: 0
- Output fields changed: 0
- Generated preview files added: 0
- Local terrain data files added: 0
- GIS files added: 0

## CI / Local Test Result

Local commands were not run by the Cloud Agent. GitHub Actions CI will be checked after pull request creation, and this record will be updated to the checked result before completion reporting.

## Interpretation

The preview CLI now has a stable documentation reference that distinguishes structured JSON from human-readable text, fixes status and file rules, and gives the next Local task a narrow regression-test scope rather than a feature-development scope.

## Limitations

This task does not execute the CLI, create files, change source or tests, add options, change schemas, generate reports, render UI surfaces, access terrain data, convert MGRS coordinates, or change scoring, LOS/Fresnel, route, or waypoint logic.

## Figure/Table Candidacy

The output-mode matrix, status-code table, JSON field lists, and future-consumer guidance are candidates for adaptation into an implementation or methodology table.

No image or rendered diagram is generated.

## Public Repository Sensitivity Check

Only repository documentation is included. No private path, sensitive coordinate, credential, secret, local dataset, GIS file, generated preview, CSV, PDF, image, QGIS project, or archive is included.

## Follow-Up Tasks

1. Task 023B-Local: add contract regression tests without changing behavior.
2. A separate report task may consume reviewed JSON files.
3. A separate UI task may consume the JSON-ready dictionary or record list.
4. Real-terrain integration remains outside the synthetic CLI contract.