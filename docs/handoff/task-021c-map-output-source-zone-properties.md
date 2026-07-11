# Task 021C Map Output Candidate Source-zone Properties

## Purpose

Task 021C connects Task 021B candidate source-zone map metadata to existing `CandidateCellMapFeature` records through an optional properties mapping.

The change is non-breaking. Existing candidate map feature construction and existing `build_map_output_package(scenario)` calls remain valid.

## Inputs

The optional attachment path accepts:

1. Existing `CandidateCellMapFeature` records.
2. A mapping keyed by candidate or cell identifier.
3. Task 021B map-ready property dictionaries as mapping values.

The current matching key is `CandidateCellMapFeature.candidate_id`, because the existing candidate feature structure does not expose a separate `cell_id` field.

## Optional candidate feature properties

`CandidateCellMapFeature` now has the final optional field:

- `candidate_source_zone_map_properties`

The field uses an empty mapping by default. Existing positional and keyword constructors therefore remain valid.

When populated, the mapping requires:

- `candidate_cell_mgrs`
- `external_coordinate_format`
- `user_coordinate_field`
- `source_zone`
- `source_sensitive`
- `source_zone_reason`

The mapping may also retain non-coordinate metadata such as `cell_id` and `internal_debug_available`.

## MGRS external coordinate handling

The user-facing candidate coordinate property is `candidate_cell_mgrs`.

`external_coordinate_format` must be `MGRS`, and `user_coordinate_field` must be `candidate_cell_mgrs`.

The validator reuses `require_mgrs_external_coordinate_field("candidate_cell_mgrs")` from the Task 020E coordinate boundary policy.

This task does not implement MGRS conversion and does not assess the geographic accuracy of caller-provided MGRS strings.

## Internal/debug coordinate handling

Existing `CandidateCellMapFeature.x_m` and `CandidateCellMapFeature.y_m` remain available as internal geometry coordinates so current map-ready construction remains compatible.

They are not user-facing coordinate metadata. The optional properties mapping rejects these internal/debug coordinate keys:

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

## Non-breaking map output compatibility

`attach_candidate_source_zone_map_properties(...)` attaches metadata by `candidate_id` and returns new frozen dataclass records.

The helper copies each metadata mapping before storing it. Extra metadata identifiers that do not match a candidate feature are allowed.

With `require_all=True`, missing metadata for any candidate raises `MapOutputError`. With `require_all=False`, unmatched candidate features remain unchanged.

`build_map_output_package(scenario)` continues to work without metadata. The optional `candidate_source_zone_metadata_by_cell_id` argument activates the attachment path only when supplied.

No existing candidate feature field is removed or renamed. Existing source-zone fields, color classes, styles, scores, and reasons remain unchanged.

## Summary fields

`summarize_map_output_package(...)` adds the following non-breaking fields:

- `candidate_source_zone_map_properties_feature_count`
- `candidate_source_zone_map_properties_missing_feature_count`
- `candidate_source_zone_map_properties_external_coordinate_format`
- `candidate_source_zone_map_properties_user_coordinate_field`

When no metadata is attached, the last two fields use `not_attached`. When metadata is present, they use `MGRS` and `candidate_cell_mgrs`.

## Test result

Synthetic tests cover:

- existing constructor compatibility
- existing package builder compatibility
- metadata attachment by candidate identifier
- MGRS coordinate metadata requirements
- internal coordinate key rejection
- required and partial attachment modes
- extra metadata identifier handling
- attached and missing summary counts
- optional package builder path
- readable attachment summary text
- absence of GIS and rendering dependencies

Cloud Agent did not execute local commands. GitHub Actions is the CI result source for this pull request.

## Overall status

Task 021C provides a non-breaking connection between Task 021B properties and current candidate map feature data.

## Limitations

This task does not:

- render maps
- implement Streamlit or Folium
- implement MGRS conversion
- assess MGRS geographic accuracy
- modify candidate scoring
- recalculate LOS or Fresnel values
- modify route scoring
- modify waypoint scoring
- read real DEM, DSM, or landcover files
- use `METADATA_MAP` files
- add GIS files
- establish field-performance results

## Public repository sensitivity check

This document includes no private absolute path, sensitive coordinate, credential, token, secret, raster file, `METADATA_MAP` file, CSV, image, PDF, QGIS project, or generated local artifact.

## Follow-up tasks

1. Add a user-facing candidate table or popup formatter that consumes the optional properties.
2. Keep rendering implementation separate from metadata validation.
3. Add MGRS conversion in a separate integration task when required.
4. Preserve internal geometry coordinates as explicitly internal implementation data.
