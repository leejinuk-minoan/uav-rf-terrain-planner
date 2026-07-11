# EXP-20260711-016 - Candidate Source-zone Map Metadata Bridge

## Experiment Purpose

Record the Task 021B bridge that converts MGRS-based candidate source-zone output records into future map-ready candidate feature properties.

## Input Data

Synthetic in-memory `CandidateSourceZoneOutputBundle` records and dummy MGRS strings only.

No real raster, `METADATA_MAP`, GIS file, map screenshot, CSV, image, PDF, or QGIS project file is used.

## Method

The task adds a pure Python candidate map source-zone metadata bridge. It accepts a Task 021A `CandidateSourceZoneOutputBundle`, copies `candidate_cell_mgrs`, source-zone, source-sensitive, source-zone reason, and internal-debug availability into `CandidateMapSourceZoneProperties`, and exposes a `to_map_properties()` dictionary for future candidate table or map popup builders.

The bridge also provides a by-cell-id mapping helper and a summary helper.

## Expected Result

- `candidate_cell_mgrs` remains the user-facing candidate coordinate property.
- `external_coordinate_format` is `MGRS`.
- Source-zone and source-sensitive metadata are preserved.
- Source-zone count and dominant source-zone summary are preserved.
- Internal coordinate keys are not default map-ready properties.
- Map rendering, MGRS conversion, candidate scoring, LOS/Fresnel, route scoring, and waypoint scoring are not changed.

## Actual Result

Implemented in the Task 021B pull request. Candidate source-zone map metadata records, map-ready property dictionaries, by-cell-id mapping helper, summary helper, synthetic tests, handoff documentation, and experiment record were added.

## Metrics

- Candidate map source-zone metadata modules added: 1
- Metadata property dataclasses added: 2
- Builder helpers added: 2
- Summary helpers added: 1
- Test files added: 1
- Handoff documents added: 1
- Real raster files added: 0
- `METADATA_MAP` files added: 0
- GIS files added: 0

## CI / Local Test Result

Local commands were not run by the Cloud Agent. GitHub Actions CI should be checked on the Task 021B pull request.

## Interpretation

This bridge provides the metadata boundary needed by future candidate table or map popup builders. It reinforces the MGRS external I/O policy by preserving `candidate_cell_mgrs` and keeping internal coordinate keys out of default map-ready properties.

## Limitations

This task does not implement map rendering, MGRS conversion, MGRS geographic accuracy checking, candidate scoring integration, LOS/Fresnel recomputation, route scoring changes, or waypoint scoring changes.

## Figure/Table Candidacy

A paper-ready schema table can show `candidate_cell_mgrs`, `external_coordinate_format`, `source_zone`, `source_sensitive`, and `source_zone_reason` as future candidate feature properties.

## Public Repository Sensitivity Check

Only source and documentation changes are included. No private absolute path, sensitive coordinate, credential, token, secret, raster file, `METADATA_MAP` file, CSV, image, PDF, QGIS project, or generated local artifact is included.

## Follow-up Tasks

1. Connect the metadata bridge to optional candidate properties in `map_outputs.py` without breaking current constructors.
2. Connect map-ready property dictionaries to future candidate table formatting.
3. Connect map-ready property dictionaries to future map popup formatting.
4. Keep internal/debug coordinates separate from default user-facing properties.
