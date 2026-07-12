# EXP-20260712-031 - Preview JSON Input Boundary Plan

## Experiment Purpose

Record the documentation-only design of a saved preview JSON input boundary for existing appendix-table stdout and explicit table-file output.

## Input Data

Existing repository source, tests, architecture documents, handoff records, experiment records, README content, and agent guidance only.

No runtime dataset or generated output is used in this task.

## Method

Review the current synthetic-only CLI, JSON output contract, appendix-table formatter, table CLI integration, focused tests, and prior task records.

Define the proposed `--input-json PATH` source, exactly-one-source policy, supported table outputs, input-file checks, decode/schema failures, status mappings, coordinate boundaries, metadata handling, generated-artifact restrictions, and a narrow Task 026B Local scope.

## Expected Result

- One architecture document defines the saved preview JSON input boundary.
- `--input-json PATH` is documented as the future saved-input selector.
- Exactly one of two source selectors is required.
- Saved input is compatible only with table stdout and explicit table-file output.
- Input read/decode/schema/formatter failures map to status 1.
- Source and unsupported-output conflicts map to status 2.
- Output-file failures remain status 3.
- Existing synthetic commands remain unchanged.
- MGRS and internal-coordinate policies remain fixed.
- Source-zone fields remain interpretation metadata.
- One focused Task 026B-Local prompt is added.
- No source or test code is changed.

## Actual Result

Implemented on the Task 026A documentation branch. The architecture plan, Task 026B prompt, handoff record, experiment record, README summary, and experiment index update were prepared without changing source or test code.

The plan introduces no runtime behavior. It separates saved-input errors from output-file errors and limits the future input path to the existing table formatter.

## Metrics

- Architecture documents added: 1
- Local implementation prompts added: 1
- Handoff documents added: 1
- Experiment records added: 1
- Proposed input options: 1
- Source selectors governed: 2
- Saved-input output modes supported: 2
- Status codes preserved: 4
- Existing synthetic commands changed: 0
- Source files changed: 0
- Test files changed: 0
- JSON fields changed: 0
- Formatter fields or columns changed: 0
- Generated input/output files added: 0

## CI / Local Test Result

Local compile, pytest, Ruff, mypy, CLI execution, JSON read/write, formatter execution, and file generation were not run by the Cloud Agent. GitHub Actions is checked after pull request creation and on the final documentation head before completion reporting.

## Interpretation

A saved reviewed preview can later become an appendix table without introducing a new schema or bypassing formatter validation. Separating source selection, input errors, and output errors preserves deterministic CLI behavior and keeps the input path narrow.

## Limitations

This task does not implement or execute JSON input, change source or tests, alter formatter behavior, generate files, access terrain data, convert MGRS, assess coordinate accuracy, recalculate scores, or render report, UI, map, or HTML content.

## Figure/Table Candidacy

The source/output compatibility matrix, status-code table, input-error taxonomy, and Task 026B acceptance criteria are candidates for an implementation or methodology appendix.

No rendered figure or generated artifact is created.

## Public Repository Sensitivity Check

Only repository Markdown documentation and index updates are included. No runtime dataset, local output, generated preview, generated table, report artifact, or private path is included.

## Follow-Up Tasks

1. Task 026B-Local: connect `--input-json PATH` to table stdout and explicit table-file output.
2. A later task may define plain-text preview reconstruction from structured JSON.
3. Separate report and UI tasks may consume reviewed preview data.
4. Real-terrain integration remains outside this input-boundary plan.
