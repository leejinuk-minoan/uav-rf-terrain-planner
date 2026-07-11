# Task 021B Candidate Source-zone Map Metadata Bridge

## Purpose

Task 021B converts a `CandidateSourceZoneOutputBundle` into future map-ready candidate feature properties.

This is a pure Python metadata bridge. It does not render maps, change scoring behavior, or connect to real raster files.

## Inputs

The bridge expects a `CandidateSourceZoneOutputBundle` from Task 021A.

Each upstream output record must already contain:

- `cell_id`
- `candidate_cell_mgrs`
- `source_zone`
- `source_sensitive`
- `source_zone_reason`
- `internal_debug_available`

## Map-ready properties

Each `CandidateMapSourceZoneProperties` record exposes map-ready property keys for future candidate tables, map popups, or feature-property builders.

The property dictionary contains:

- `cell_id`
- `candidate_cell_mgrs`
- `external_coordinate_format`
- `user_coordinate_field`
- `source_zone`
- `source_sensitive`
- `source_zone_reason`
- `internal_debug_available`

`source_zone` is exported as a string value rather than as an enum object.

## MGRS external coordinate handling

The user-facing candidate coordinate property is `candidate_cell_mgrs`.

`external_coordinate_format` is `MGRS`.

The bridge uses `require_mgrs_external_coordinate_field("candidate_cell_mgrs")` to preserve the Task 020E external coordinate guardrail.

This task is not MGRS conversion. It does not verify the geographic accuracy of dummy or caller-provided MGRS strings.

## Source-zone metadata handling

The bridge preserves the Task 021A source-zone metadata:

- source zone
- source-sensitive flag
- source-zone reason

The metadata summary includes:

- candidate map metadata count
- user coordinate field
- external coordinate format
- ESA-derived count
- WMS gap-filled count
- DEM-only fallback count
- mixed-boundary count
- source-sensitive count
- dominant source zone
- reason

## Internal/debug coordinate handling

Internal coordinates are not default map-ready properties.

The following keys are not included in `to_map_properties()` output:

- `x_m`
- `y_m`
- `row`
- `col`
- `epsg5179_x_m`
- `epsg5179_y_m`
- `wgs84_lat`
- `wgs84_lon`
- `local_x_m`
- `local_y_m`
- `raster_row`
- `raster_col`

If future debug views need these values, they should be added in a separate explicitly internal/debug path.

## Map output compatibility

Future candidate table or map popup builders can consume this metadata bundle.

Future map output builders can merge the returned property dictionaries into candidate map feature properties.

This task does not change `map_outputs.py` constructor requirements and does not implement rendering behavior.

## Test result

Synthetic tests cover:

- converting `CandidateSourceZoneOutputBundle` into candidate map metadata
- preserving `candidate_cell_mgrs`
- preserving `external_coordinate_format = MGRS`
- preserving `user_coordinate_field = candidate_cell_mgrs`
- exporting source-zone string values
- preserving source-sensitive flags and reasons
- source-zone count summary
- source-sensitive count summary
- dominant source-zone summary
- by-cell-id mapping creation
- duplicate cell-id error handling
- wrong bundle type error handling
- empty metadata record error handling
- absence of internal coordinate keys
- absence of GIS/raster/rendering imports

Cloud Agent does not run local commands. GitHub Actions CI is the verification source for this PR.

## Overall status

Task 021B adds the bridge between MGRS-based candidate source-zone output records and future map-ready candidate feature properties.

## Limitations

This task does not:

- render maps
- implement MGRS conversion
- verify MGRS geographic accuracy
- change candidate scoring
- recalculate LOS/Fresnel values
- change route scoring
- change waypoint scoring
- read real DEM/DSM/landcover files
- use `METADATA_MAP` files
- add GIS files
- provide operational validation

## Public repository sensitivity check

This handoff document includes no private absolute path, sensitive coordinate, credential, token, secret, raster file, `METADATA_MAP` file, CSV, image, PDF, QGIS project, or generated local artifact.

## Follow-up tasks

1. Connect this bridge to optional candidate properties in `map_outputs.py` without breaking current constructors.
2. Connect the returned property dictionaries to future candidate table formatting.
3. Connect the returned property dictionaries to future map popup formatting.
4. Keep internal/debug coordinates separate from default user-facing properties.
