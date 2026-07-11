# EXP-20260711-014 - MGRS External I/O Boundary Policy

## Experiment Purpose

Record the Task 020E policy and guardrail helper that define MGRS as the external coordinate format for user inputs and user-facing outputs.

## Input Data

Repository source and documentation only.

No real raster, `METADATA_MAP`, GIS file, map screenshot, CSV, image, PDF, or QGIS project file is used.

## Method

The task adds an architecture policy document, a small coordinate I/O policy helper, tests for approved MGRS field names and internal/debug coordinate field names, a README note, and this sharded experiment record.

## Expected Result

- External input coordinate fields are represented as MGRS.
- External output coordinate fields are represented as MGRS.
- Internal WGS84, EPSG:5179, local x/y, and raster row/col fields are recognized as internal/debug fields.
- Task 020D aggregate-only smoke output remains compatible because it did not print coordinates.
- No UI, map rendering, scoring integration, LOS/Fresnel recomputation, or end-to-end coordinate conversion is implemented.

## Actual Result

Policy and guardrail helper were added in this branch. PR and CI status should be checked on the corresponding Task 020E pull request.

## Metrics

- Architecture policy documents added: 1
- Coordinate I/O helper modules added: 1
- Test files added: 1
- Experiment records added: 1
- Real raster files added: 0
- `METADATA_MAP` files added: 0
- GIS files added: 0

## CI / Local Test Result

Local commands were not run by the Cloud Agent. GitHub Actions CI should be used for install, syntax, pytest, ruff, and mypy checks after the pull request is created.

## Interpretation

The project now has a single policy reference for separating external MGRS fields from internal computation coordinates. This is a schema and documentation guardrail, not a finished coordinate conversion workflow.

## Limitations

This task does not implement actual MGRS to EPSG:5179 end-to-end conversion, UI field rendering, map popup behavior, candidate scoring integration, LOS/Fresnel recomputation, or field validation.

## Figure/Table Candidacy

A short policy table can be used in the paper to separate user-facing MGRS fields from internal/debug coordinate fields.

## Public Repository Sensitivity Check

Only source and documentation changes are included. No private absolute path, sensitive coordinate, credential, token, secret, raster file, `METADATA_MAP` file, CSV, image, PDF, QGIS project, or generated local artifact is included.

## Follow-up Tasks

1. Add explicit MGRS fields to user-facing candidate, route, waypoint, and map output records.
2. Add local validation for MGRS to projected-coordinate conversion.
3. Update future UI and report formatting so MGRS is the default coordinate display.
4. Add end-to-end tests when coordinate conversion and display layers are implemented.
