# EXP-20260711-015 - Candidate Source-zone Output Metadata Scaffold

## Experiment Purpose

Record the Task 021A scaffold that converts candidate source-zone assignment results into candidate output metadata records using `candidate_cell_mgrs` as the user-facing coordinate field.

## Input Data

Repository source and documentation only. Synthetic in-memory candidate source-zone assignments are used by tests.

No real raster, `METADATA_MAP`, GIS file, map screenshot, CSV, image, PDF, or QGIS project file is used.

## Method

The task adds a pure Python candidate output source-zone module. It accepts Task 020C `CandidateSourceZoneAssignment` records and a caller-provided `cell_id -> candidate_cell_mgrs` mapping. The module does not convert coordinates. It preserves source-zone metadata and produces output records with `candidate_cell_mgrs`, source-zone, source-sensitive flag, source-zone reason, and summary counts.

## Expected Result

- `candidate_cell_mgrs` is required for every output record.
- Internal/debug coordinates from assignment records are not used as default user-facing output fields.
- ESA-derived, WMS gap-filled, DEM-only fallback, and mixed-boundary counts are preserved.
- Source-sensitive count and dominant source zone are summarized.
- Existing scoring, LOS/Fresnel, route, and waypoint computations are not invoked.
- Real terrain files, local raster data, and map rendering are not used.

## Actual Result

Implemented in branch `agent/task-021a-candidate-source-zone-output-scaffold`. PR and CI status should be checked on the corresponding Task 021A pull request.

## Metrics

- Candidate source-zone output modules added: 1
- Candidate output record dataclasses added: 2
- Builder helpers added: 1
- Summary helpers added: 1
- Test files added: 1
- Real raster files added: 0
- `METADATA_MAP` files added: 0
- GIS files added: 0

## CI / Local Test Result

Local commands were not run by the Cloud Agent. GitHub Actions CI should be used for install, syntax, pytest, ruff, and mypy checks after the pull request is created.

## Interpretation

This scaffold provides a candidate output metadata boundary between source-zone assignment and later user-facing candidate tables or map popups. It reinforces the Task 020E MGRS external I/O policy by requiring `candidate_cell_mgrs` and keeping projected or raster coordinates out of the default output record.

## Limitations

This task does not implement MGRS conversion, UI behavior, map popup rendering, candidate scoring integration, LOS/Fresnel recomputation, or field validation.

## Figure/Table Candidacy

A short table separating `candidate_cell_mgrs`, source-zone, and source-sensitive status can be used in the paper as an output-schema example.

## Public Repository Sensitivity Check

Only source and documentation changes are included. No private absolute path, sensitive coordinate, credential, token, secret, raster file, `METADATA_MAP` file, CSV, image, PDF, QGIS project, or generated local artifact is included.

## Follow-up Tasks

1. Connect candidate output source-zone records to future candidate table and map popup formatting.
2. Add actual MGRS conversion in a separate local or integration task.
3. Add optional debug views that label internal projected coordinates explicitly when needed.
4. Preserve source-sensitive flags in later candidate analysis outputs.
