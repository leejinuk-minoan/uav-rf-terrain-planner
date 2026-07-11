# Task 021A Candidate Source-zone Output Metadata Scaffold

## Purpose

Task 021A adds a pure Python scaffold that converts `CandidateSourceZoneAssignment` results into a candidate output metadata bundle for later user-facing candidate tables or map popups.

This task preserves the existing scoring and terrain-analysis pipeline. It only adds the candidate source-zone output metadata boundary.

## Inputs

The scaffold expects two inputs:

1. `CandidateSourceZoneAssignment` from the Task 020C candidate-grid source-zone assignment layer.
2. A caller-provided `Mapping[str, str]` from `cell_id` to `candidate_cell_mgrs`.

The caller must provide `candidate_cell_mgrs` values. This task does not create or convert those MGRS strings.

## Output records

Each `CandidateSourceZoneOutputRecord` contains:

- `cell_id`
- `candidate_cell_mgrs`
- `source_zone`
- `source_sensitive`
- `source_zone_reason`
- `internal_debug_available`

The user-facing candidate coordinate field is `candidate_cell_mgrs`.

## MGRS external coordinate handling

The Task 020E external coordinate policy is preserved. User-facing candidate coordinate output uses MGRS.

`candidate_cell_mgrs` is required and must be supplied by the caller. The scaffold checks the field name with `require_mgrs_external_coordinate_field("candidate_cell_mgrs")`.

This task does not implement MGRS conversion. It also does not verify the geographic accuracy of the provided MGRS string.

## Source-zone metadata handling

The scaffold preserves the following source-zone metadata from assignment records:

- source zone
- source-sensitive flag
- source-zone reason

The output summary provides:

- source-zone counts
- source-sensitive count
- dominant source zone
- reason
- external coordinate format

The external coordinate format is `MGRS`.

## Internal/debug coordinate handling

Internal/debug coordinates are not part of the default output record.

The following internal/debug coordinate fields are not added to `CandidateSourceZoneOutputRecord`:

- `x_m`
- `y_m`
- `row`
- `col`
- `epsg5179_x_m`
- `epsg5179_y_m`

If later debug views need these values, they should be explicitly marked as internal/debug and kept separate from the default user-facing output record.

## Map output compatibility

Future map-ready output, candidate tables, or map popups can consume the output bundle.

When a user-facing coordinate is displayed, the default coordinate must be MGRS. Internal projected or raster coordinates should either be omitted or explicitly marked as internal/debug.

This task does not render maps.

## Test result

Synthetic tests cover:

- `candidate_cell_mgrs` use in output records
- source-zone count preservation
- source-sensitive count preservation
- dominant zone summary
- external coordinate format summary
- missing or empty `candidate_cell_mgrs` errors
- absence of internal/debug coordinate fields in the default output record
- handoff document boundary wording

Cloud Agent did not run local commands. GitHub Actions CI is the verification source for this PR.

## Overall status

Task 021A provides the missing candidate source-zone output metadata boundary and is ready for GPT Master review after the review-fix commit CI is checked.

## Limitations

This task does not:

- implement MGRS conversion
- verify MGRS geographic accuracy
- read real DEM/DSM/landcover files
- use `METADATA_MAP` files
- add GIS files
- render maps
- change candidate scoring
- recalculate LOS/Fresnel values
- change route scoring
- change waypoint scoring
- provide operational validation

## Public repository sensitivity check

This handoff document includes no private absolute path, sensitive coordinate, credential, token, secret, raster file, `METADATA_MAP` file, CSV, image, PDF, QGIS project, or generated local artifact.

## Follow-up tasks

1. Connect this output bundle to future candidate table formatting.
2. Connect this output bundle to future map popup formatting.
3. Implement MGRS conversion in a separate integration task when required.
4. Keep internal/debug coordinates separate from default user-facing output records.
