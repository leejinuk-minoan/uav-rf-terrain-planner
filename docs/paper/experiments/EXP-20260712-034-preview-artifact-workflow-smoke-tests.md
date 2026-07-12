# EXP-20260712-034 - Preview Artifact Workflow Smoke Tests

## Experiment Purpose

Verify that the nine documented preview artifact workflow commands remain consistent with the implemented CLI contract.

## Input Data

Existing synthetic preview data and temporary saved JSON/table artifacts under pytest `tmp_path`.

## Method

Call `run_preview_cli()` for each documented workflow and validate status, JSON semantics, table semantics, saved-input reuse, row limiting, overwrite protection, coordinate boundaries, and temporary artifact containment.

## Expected Result

All workflows return the documented result without source changes or repository artifacts.

## Actual Result

All focused and repository-wide tests passed locally. Runtime artifacts remained under temporary test paths.

## Metrics

- Documented workflows covered: 9
- Focused smoke tests: 3
- Source files changed: 0
- Generated artifacts committed: 0

## CI / Local Test Result

Local compile, pytest, Ruff, mypy, diff, and policy checks are recorded in the Task 027B PR. CI is recorded after push.

## Limitations

This verifies software workflow consistency, not real-terrain or field performance.

## Public Repository Sensitivity Check

No private path, terrain raster, generated preview/table, CSV/PDF/image, QGIS project, report, or archive is committed.
