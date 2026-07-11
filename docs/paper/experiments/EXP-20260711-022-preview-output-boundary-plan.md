# EXP-20260711-022 - Preview Output Boundary Plan

## Experiment Purpose

Record the documentation-only decision that separates the current MGRS candidate preview pipeline from later CLI, report, and persistent file-output implementation work.

## Input Data

Existing repository source files, architecture documents, handoff records, experiment records, README content, and agent-operation guidance only.

No real raster, `METADATA_MAP` content, GIS file, map screenshot, CSV file, image, PDF, or QGIS project file is used.

## Method

Review the current preview object, JSON-ready dictionary, plain-text formatter, and synthetic preview smoke. Compare candidate output surfaces, define the recommended implementation order, separate Cloud planning from Local implementation, and prepare a focused Task 022B-Local prompt.

The review covers CLI stdout, JSON stdout, JSON file output, plain-text file output, future UI surfaces, and paper/report appendix use.

## Expected Result

- One architecture document defines the preview output boundary.
- Output surface candidates are compared.
- The recommended order starts with a minimal stdout CLI.
- Persistent file output is deferred to Task 022C or later.
- Cloud and Local responsibilities are separated.
- A complete Task 022B-Local prompt is added.
- `candidate_cell_mgrs` and `MGRS` remain the external candidate coordinate contract.
- Internal/debug coordinate fields remain outside user outputs.
- Source-zone interpretation metadata remains separate from scoring.
- No source or test code is changed.

## Actual Result

Implemented on the Task 022A branch. The architecture plan, Local Task 022B prompt, handoff record, experiment record, README summary, and experiment index entry were added. Pull request and CI status are finalized after PR creation.

## Metrics

- Architecture documents added: 1
- Local implementation prompts added: 1
- Handoff documents added: 1
- Experiment records added: 1
- Output surface candidates compared: 5
- Source files changed: 0
- Test files changed: 0
- CLI implementations added: 0
- File-writing implementations added: 0
- Generated diagram files added: 0
- Local terrain data files added: 0
- GIS files added: 0

## CI / Local Test Result

Local commands were not run by the Cloud Agent. GitHub Actions CI will be checked after pull request creation, and this record will be updated to the checked result before completion reporting.

## Interpretation

The next Local task can be kept small by using the existing synthetic smoke and preview contracts. A stdout-only CLI provides a reviewable user-output boundary without introducing path management, overwrite behavior, generated artifacts, or report/UI concerns.

## Limitations

This task does not execute code, implement a CLI, write files, generate reports, render maps, tables, popups, HTML, or application UI, convert MGRS coordinates, assess MGRS geographic correctness, modify scoring, recalculate LOS/Fresnel values, or change route and waypoint scoring.

## Figure/Table Candidacy

The output-surface comparison table and Cloud-versus-Local responsibility split are candidates for adaptation into a project architecture or methodology table.

No image or rendered diagram is generated in this task.

## Public Repository Sensitivity Check

Only repository documentation is included. No private path, sensitive coordinate, credential, secret, local dataset, GIS file, generated media, CSV, PDF, QGIS project, or output artifact is included.

## Follow-Up Tasks

1. Task 022B-Local: implement the synthetic stdout CLI and focused tests.
2. Task 022C-Local: define persistent JSON/text file output only if required.
3. Review whether later UI consumers should use display records directly or the JSON-ready preview dictionary.