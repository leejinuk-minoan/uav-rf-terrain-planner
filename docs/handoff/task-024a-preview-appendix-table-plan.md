# Task 024A Preview Appendix Table Boundary Plan

## Purpose

Task 024A documents the boundary for transforming the reviewed preview JSON dictionary into a paper appendix table or developer review table before any formatter, report, file-output, or UI implementation is added.

This task is documentation-only. It preserves the Tasks 023A/023B preview JSON contract and defines a narrow Task 024B Local implementation scope.

## Documents Added

- `docs/architecture/preview-appendix-table-plan.md`
- `docs/prompts/local-task-024b-preview-appendix-table-formatter.md`
- `docs/handoff/task-024a-preview-appendix-table-plan.md`
- `docs/paper/experiments/EXP-20260712-027-preview-appendix-table-plan.md`

README receives a short Task 024A summary and the experiment index receives one EXP-20260712-027 entry.

## Current Input Contract

The planned formatter consumes the existing preview JSON dictionary directly or a dictionary loaded by a caller from a reviewed JSON file.

Required top-level fields:

```text
title
external_coordinate_format
user_coordinate_field
record_count
source_sensitive_count
records
summary
reason
```

Required record fields:

```text
candidate_id
candidate_cell_mgrs
external_coordinate_format
user_coordinate_field
color_class
color_name
overall_score
shielding_stability_score
source_zone
source_sensitive
source_zone_reason
candidate_reason
display_label
```

Task 024A does not add, remove, rename, or reinterpret JSON fields. `row_no` is defined only as a future table-display value derived from record order.

## Intended Consumers

| Consumer | Recommended input | Planned output |
|---|---|---|
| Paper appendix preparation | Preview JSON file or dictionary | Markdown/plain-text table string |
| Developer review | Preview JSON dictionary | Markdown/plain-text table string |
| Future report generator | Preview JSON file | Separate later report task |
| Future UI table/card | JSON-ready record list | Separate later UI task |

## Recommended Table Columns

```text
row_no
candidate_id
candidate_cell_mgrs
color_class
color_name
overall_score
shielding_stability_score
source_zone
source_sensitive
source_zone_reason
candidate_reason
```

The default formatter preserves JSON record order. `row_no` starts at 1 and is not a rank. Existing score values are displayed only; they are not recalculated, normalized, or used to reorder rows.

## MGRS External Coordinate Handling

The user-facing coordinate boundary remains:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
```

Task 024A and the proposed Task 024B do not implement MGRS conversion and do not assess the geographic accuracy of supplied or synthetic placeholder MGRS text.

## Internal/Debug Coordinate Handling

The following fields remain excluded from the table contract:

```text
x_m
y_m
row
col
epsg5179_x_m
epsg5179_y_m
wgs84_lat
wgs84_lon
local_x_m
local_y_m
raster_row
raster_col
```

Task 024B should reject preview input containing those keys at the top level or inside records.

## Source-Zone Metadata Handling

The table may display:

```text
source_zone
source_sensitive
source_zone_reason
```

These values remain interpretation metadata. They do not affect candidate scoring, LOS/Fresnel values, route scoring, or waypoint scoring.

## Recommended Task 024B Scope

Task 024B-Local should add only:

- `src/uav_rf_terrain/preview_appendix_table.py`
- `tests/test_preview_appendix_table.py`
- a pure Python `format_preview_appendix_table(...)` function or equivalently narrow API
- validation of the existing JSON contract
- preserved record order and one-based display row numbers
- the recommended table columns
- optional positive `max_rows`
- deterministic omitted-row text
- MGRS and source-zone metadata preservation
- internal/debug coordinate rejection
- focused tests and concise task records

Task 024B must return a string only. It must not add a CLI option, write a file, generate a report, render HTML, or implement a UI surface.

## Test/CI Result

Task 024A changes no source or test code. Cloud Agent does not claim local command execution. GitHub Actions is checked after pull request creation and rechecked on the final documentation head.

## Overall Status

The reviewed preview JSON contract now has a separate appendix-table boundary. The next Local task can implement a small formatter without redefining CLI, file, terrain, scoring, route, waypoint, report, or UI behavior.

## Limitations

Task 024A does not:

- implement or execute a formatter
- change source or tests
- add a CLI option
- change JSON or plain-text preview output
- write table or report files
- generate a report
- render a UI table, card, popup, HTML page, map, or diagram
- access real DEM, DSM, landcover, or `METADATA_MAP`
- add GIS dependencies
- convert MGRS coordinates
- assess MGRS geographic accuracy
- change candidate scoring, LOS/Fresnel, route, or waypoint logic
- add vehicle-control or autopilot output

## Public Repository Sensitivity Check

Only repository Markdown documentation and index updates are included. No private absolute path, sensitive coordinate, credential, token, secret, terrain raster, `METADATA_MAP` file, GIS file, generated table, JSON output, text output, CSV, PDF, image, diagram, QGIS project, or archive is included.

## Follow-Up Tasks

1. Task 024B-Local: implement the pure Python preview appendix table formatter and focused tests.
2. A later task may add explicit table-file output after path, overwrite, encoding, cleanup, and generated-artifact policies are reviewed.
3. A later report task may consume a reviewed table string.
4. A later UI task may consume the JSON-ready record list independently.
5. Real-terrain integration remains outside this synthetic preview-consumer boundary.
