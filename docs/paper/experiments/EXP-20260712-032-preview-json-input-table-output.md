# EXP-20260712-032 - Preview JSON Input Table Output

## Experiment Purpose

Verify explicit saved-preview JSON input for the existing table stdout and table-file projections.

## Input Data

Temporary UTF-8 JSON files containing the reviewed synthetic preview dictionary and deliberately invalid variants.

## Method

Exercise valid stdout/file output, row limiting, overwrite behavior, source selection, unsupported output combinations, decode and top-level failures, formatter contract failures, output path failures, synthetic-helper avoidance, and existing synthetic compatibility.

## Expected Result

Saved input is converted only through the reviewed formatter, with deterministic status codes and no partial or replaced output on input failure.

## Actual Result

Focused and repository-wide tests passed locally. Manual temporary JSON-to-table smoke completed and generated files were cleaned up.

## Metrics

- New source selector: 1
- Supported saved-input projections: 2
- Status meanings preserved: 4
- Formatter behavior changes: 0
- Generated files committed: 0

## CI / Local Test Result

Local compile, pytest, Ruff, mypy, diff checks, and manual smoke are recorded in the Task 026B PR. CI is recorded after push.

## Interpretation

A reviewed preview JSON artifact can be reused for deterministic table inspection without invoking synthetic generation or expanding into report, UI, terrain, or scoring behavior.

## Limitations

Only the existing preview contract is accepted. MGRS geographic correctness and real-terrain outcomes are not evaluated.

## Public Repository Sensitivity Check

No private path, saved input, generated table, terrain raster, CSV/PDF/image, report, QGIS project, or archive is committed.
