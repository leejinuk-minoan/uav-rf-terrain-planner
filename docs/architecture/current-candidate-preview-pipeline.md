# Current Candidate Preview Pipeline

## Purpose

This document records the current candidate preview pipeline implemented across Tasks 021C through 021F. It defines the object boundaries, user-facing coordinate policy, source-zone interpretation metadata, serialization-ready output, and the work that remains outside the current pipeline.

## Pipeline Summary

```text
Synthetic scenario
→ candidate map features
→ source-zone MGRS metadata attachment
→ candidate display records
→ candidate display preview object
→ JSON-ready preview dictionary
→ plain-text preview
```

The current implementation is an in-memory analysis and preview pipeline. It does not render a map, table, popup, HTML page, or application UI, and it does not write preview files.

## Stage 1 - Candidate Map Features

Task 021C uses `CandidateCellMapFeature` as the map-ready candidate object. Existing internal geometry fields such as `x_m` and `y_m` remain available for internal construction, while the optional `candidate_source_zone_map_properties` mapping carries user-facing MGRS and source-zone metadata when attached.

The attachment path is non-breaking: existing `CandidateCellMapFeature` construction and `build_map_output_package(scenario)` calls remain valid when no metadata mapping is provided.

## Stage 2 - Source-Zone MGRS Metadata Attachment

The optional candidate metadata mapping is attached by `candidate_id`. Its user-facing coordinate contract is:

- `candidate_cell_mgrs`: caller-supplied candidate coordinate text
- `external_coordinate_format`: `MGRS`
- `user_coordinate_field`: `candidate_cell_mgrs`

The same mapping preserves:

- `source_zone`
- `source_sensitive`
- `source_zone_reason`
- optional non-coordinate interpretation metadata such as `cell_id` and `internal_debug_available`

Internal/debug coordinate keys are not accepted in this user-facing metadata mapping.

## Stage 3 - Candidate Display Records

Task 021D converts candidate map features with attached metadata into `CandidateDisplayRecord` values collected in a `CandidateDisplayBundle`.

Each record preserves the candidate identifier, MGRS coordinate, color class, color name, score fields, source-zone interpretation fields, candidate reason, and a display label. `to_display_dict()` returns primitive string, float, and boolean values rather than dataclass or enum objects.

The formatter prepares data for later tables, detail panels, popups, or UI cards, but it does not implement those surfaces.

## Stage 4 - Candidate Display Preview

Task 021E converts a `CandidateDisplayBundle` into:

1. `CandidateDisplayPreview`
2. a JSON-ready preview dictionary
3. a plain-text preview string

The preview object stores record counts, source-sensitive counts, copied primitive records, the display summary, and a reason string. The JSON-ready helper converts tuple records to a list and copies mappings. The plain-text helper produces a readable review format and supports an optional positive record limit with an omitted-record count.

## Stage 5 - Synthetic Preview Smoke

Task 021F connects the existing synthetic scenario to the preview boundary in memory. It builds candidate map features, assigns deterministic placeholder MGRS strings, attaches source-zone metadata, builds display records, and produces preview object, dictionary, and text outputs.

The placeholder MGRS strings illustrate the schema only. They are not produced through coordinate conversion and are not assessed for geographic accuracy.

## Current Pipeline Schema

| Stage | Input object | Output object | User-facing coordinate field | Internal/debug coordinate exposure | Rendering/file-output status | Implemented by task |
|---|---|---|---|---|---|---|
| Candidate map feature stage | Candidate scoring and classification outputs | `CandidateCellMapFeature` | No user-facing coordinate by default | `x_m` and `y_m` remain internal geometry | No rendering or file output | Task 021C |
| Source-zone metadata attachment | Candidate map features plus metadata mapping | `CandidateCellMapFeature` with `candidate_source_zone_map_properties` | `candidate_cell_mgrs` | Internal coordinate keys are rejected from the optional metadata mapping | No rendering or file output | Task 021C |
| Candidate display formatter | Candidate map features with attached MGRS metadata | `CandidateDisplayBundle` containing `CandidateDisplayRecord` values | `candidate_cell_mgrs` | Internal geometry is not copied into display records or dictionaries | No table, popup, or map rendering | Task 021D |
| Candidate preview object | `CandidateDisplayBundle` | `CandidateDisplayPreview` | `candidate_cell_mgrs` | Internal coordinate keys are excluded | No file writing or UI rendering | Task 021E |
| JSON-ready preview | `CandidateDisplayBundle` | JSON-ready preview dictionary | `candidate_cell_mgrs` | Internal coordinate keys are excluded | Serialization-ready data only; no file writing | Task 021E |
| Plain-text preview | `CandidateDisplayBundle` | Plain-text preview string | `candidate_cell_mgrs` | Internal coordinate values are not formatted | Text returned in memory; no file writing | Task 021E |
| Synthetic preview smoke | Synthetic scenario and placeholder MGRS metadata | `SyntheticCandidatePreviewSmokeResult` | `candidate_cell_mgrs` | Map feature geometry remains internal and is not propagated into preview output | In-memory smoke only | Task 021F |

## User-Facing Coordinate Boundary

All user-facing candidate coordinates use `candidate_cell_mgrs`. The external coordinate format is `MGRS`.

The current pipeline expects the caller to provide MGRS text. It does not implement MGRS conversion and does not assess the geographic accuracy of supplied or placeholder MGRS strings.

## Internal/Debug Coordinate Boundary

The following values are internal/debug computation or geometry fields and are not part of the candidate preview schema:

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

These values may remain in internal map feature or raster-processing layers, but they are not copied into display records, JSON-ready preview records, or plain-text preview rows.

## Source-Zone Interpretation Boundary

Source-zone fields are interpretation metadata attached to candidate outputs:

- `source_zone`: textual source category such as ESA-derived, WMS gap-filled, DEM-only fallback, or mixed-boundary
- `source_sensitive`: boolean indicating that interpretation depends on a non-ESA-only source condition or boundary mixture
- `source_zone_reason`: concise reason describing the source-zone interpretation

These fields do not alter candidate scoring, LOS/Fresnel values, route scoring, or waypoint scoring in the current pipeline.

## JSON-Ready Preview Schema

The top-level preview dictionary contains:

- `title`
- `external_coordinate_format`
- `user_coordinate_field`
- `record_count`
- `source_sensitive_count`
- `records`
- `summary`
- `reason`

Each item in `records` contains the principal fields:

- `candidate_id`
- `candidate_cell_mgrs`
- `external_coordinate_format`
- `user_coordinate_field`
- `color_class`
- `color_name`
- `overall_score`
- `shielding_stability_score`
- `source_zone`
- `source_sensitive`
- `source_zone_reason`
- `candidate_reason`
- `display_label`

`candidate_cell_mgrs` is the user-facing candidate coordinate, and `external_coordinate_format` is `MGRS`. The dictionary contains primitive values, lists, and dictionaries rather than dataclass or enum objects. It does not contain local metric coordinates, raster indices, EPSG:5179 components, or WGS84 components.

## Plain-Text Preview Schema

The current plain-text format follows this schema illustration:

```text
Candidate display preview
External coordinate format: MGRS
User coordinate field: candidate_cell_mgrs
Records: 5
Source-sensitive records: 3
- candidate-green | 52S CG 00000 00000 | green | score=90.0 | source_zone=esa_derived
... 3 additional record(s) omitted.
```

Actual identifiers, colors, scores, source-zone values, record counts, and omitted counts depend on the input bundle. The example illustrates the output schema and is not a runtime outcome commitment.

## Paper Figure/Table Candidacy

This pipeline is suitable for two paper-supporting artifacts:

1. **Pipeline figure candidate:** a left-to-right conceptual flow from synthetic scenario records through map feature metadata, display records, preview object, JSON-ready dictionary, and plain-text preview.
2. **Schema table candidate:** the current Markdown table can be adapted into a paper table comparing input/output objects, coordinate boundaries, internal-field exposure, and implementation status.

No diagram image is generated in this task. A future paper-production task may create a final visual using the documented stages after review.

## Current Limitations

The current pipeline does not:

- access real DEM, DSM, or landcover data
- access `METADATA_MAP`
- convert MGRS coordinates
- assess MGRS geographic accuracy
- render maps, tables, popups, HTML, or application UI
- write JSON, text, image, or report files
- provide a command-line interface
- change candidate scoring
- recalculate LOS or Fresnel values
- change route or waypoint scoring

## Follow-Up Tasks

1. Define the boundary between Cloud-designed preview/report contracts and Local implementation of CLI or file-output behavior.
2. Decide whether a future UI consumes the display bundle directly or consumes the JSON-ready preview dictionary.
3. Create a reviewed paper figure or final paper table in a separate artifact task.
4. Preserve MGRS as the user-facing candidate coordinate boundary and keep internal geometry fields outside preview outputs.
