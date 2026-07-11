# EXP-20260711-017 - Map Output Candidate Source-zone Properties

## Experiment Purpose

Record the Task 021C non-breaking attachment path from Task 021B candidate source-zone map metadata into existing candidate map feature records.

## Input Data

Synthetic in-memory map features and dummy MGRS metadata only.

No real raster, `METADATA_MAP`, GIS file, map screenshot, CSV, image, PDF, or QGIS project file is used.

## Method

The task adds an optional `candidate_source_zone_map_properties` field to `CandidateCellMapFeature`, validates MGRS-based metadata properties, and provides an attachment helper keyed by `candidate_id`.

`build_map_output_package(...)` accepts an optional metadata mapping while preserving the existing one-argument call.

Summary helpers count attached and missing metadata records and report the external coordinate format and user coordinate field.

## Expected Result

- Existing candidate feature construction remains valid without metadata.
- Existing `build_map_output_package(scenario)` calls remain valid.
- Optional metadata attaches by candidate identifier.
- `candidate_cell_mgrs` remains the user-facing coordinate property.
- `external_coordinate_format` remains `MGRS`.
- Internal geometry coordinates remain outside the optional user-facing properties mapping.
- Existing scoring and route/waypoint processing remain unchanged.

## Actual Result

Implemented in the Task 021C pull request. Optional candidate properties, MGRS metadata validation, attachment helper, optional package-builder path, summary fields, synthetic tests, handoff documentation, and experiment record were added.

## Metrics

- Existing candidate feature fields removed: 0
- Existing required constructor fields added: 0
- Optional candidate metadata fields added: 1
- Metadata attachment helpers added: 1
- Optional package-builder parameters added: 1
- Summary fields added: 4
- Test files added: 1
- Handoff documents added: 1
- Real raster files added: 0
- `METADATA_MAP` files added: 0
- GIS files added: 0

## CI / Local Test Result

Local commands were not run by the Cloud Agent. GitHub Actions CI will be checked after the Task 021C pull request is created.

## Interpretation

The optional properties field provides a bridge from source-zone metadata into current map-ready candidate records without replacing internal geometry fields or changing current constructors.

The user-facing coordinate property remains MGRS-based, while `x_m` and `y_m` continue to serve internal geometry construction.

## Limitations

This task does not implement map rendering, Streamlit/Folium behavior, MGRS conversion, MGRS geographic accuracy assessment, scoring changes, LOS/Fresnel recalculation, route scoring changes, or waypoint scoring changes.

## Figure/Table Candidacy

A paper-ready schema table can compare the existing internal geometry fields with the optional user-facing candidate metadata properties.

## Public Repository Sensitivity Check

Only source and documentation changes are included. No private absolute path, sensitive coordinate, credential, token, secret, raster file, `METADATA_MAP` file, CSV, image, PDF, QGIS project, or generated local artifact is included.

## Follow-up Tasks

1. Add a candidate table or popup formatter that consumes the optional metadata.
2. Keep map rendering separate from this metadata attachment layer.
3. Add MGRS conversion in a separate integration task when required.
4. Preserve backward compatibility for existing map-output constructors.
