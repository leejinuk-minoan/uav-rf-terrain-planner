# Preview Appendix Table Boundary Plan

## Purpose

This document defines the boundary for transforming the reviewed preview JSON output into a paper appendix table or a developer review table. Task 024A is documentation-only. It does not implement a formatter, add a CLI option, write a table file, generate a report, or render a UI surface.

The immediate follow-up is a narrow Local task that may add one pure Python formatter returning a Markdown/plain-text table string while preserving the existing preview JSON contract.

> Current implementation note: This document records an earlier planning boundary. For the implemented preview artifact workflow, see `docs/architecture/preview-artifact-workflow.md`, `docs/usage/preview-artifact-workflow.md`, and `tests/test_preview_artifact_workflow_smoke.py`.

## Current Input Contract

The formatter input is the preview JSON dictionary already fixed by Tasks 023A and 023B. The same semantic dictionary may be supplied directly in memory or loaded by a caller from an existing JSON file produced by the reviewed preview CLI.

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

The current JSON fields must not be added, removed, renamed, reordered as a contract requirement, or reinterpreted by Task 024B. `row_no` is not a preview JSON field. It is a display-only table value derived from record order.

The preview JSON contract is an established input boundary. A later formatter validates and consumes it; it does not redefine it.

## Intended Consumers

| Consumer | Recommended input | Output type | Notes |
|---|---|---|---|
| Paper appendix table | Preview JSON file or dictionary | Markdown/plain-text table string | Implemented only in a separate Local formatter task |
| Developer review table | Preview JSON dictionary | Markdown/plain-text table string | For inspection only |
| Future report generator | Preview JSON file | Later separate task | No report generation in Task 024A or Task 024B |
| Future UI table/card | JSON-ready record list | Later separate task | No UI rendering in Task 024A or Task 024B |

Structured consumers should use the preview JSON dictionary or record list rather than parse the existing human-readable CLI preview.

## Table Output Boundary

The Task 024B output may be one deterministic string representing a Markdown/plain-text table. It is a presentation projection of the reviewed JSON records.

The table layer may:

- validate the documented top-level and record fields
- preserve record order
- derive a one-based display row number
- format existing score values without recalculation
- display MGRS candidate coordinates
- display source-zone interpretation metadata
- limit visible rows when an explicit positive `max_rows` value is supplied
- append a concise omitted-row line when rows are limited
- return the completed table as a string

The table layer must not:

- mutate the input dictionary or records
- add, remove, or rename preview JSON fields
- automatically sort or rank records
- recalculate or normalize scores
- write a file
- add a preview CLI option
- generate a report
- render HTML or UI components

## Recommended Table Columns

The default Task 024B column candidates are:

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

`row_no` is the only derived display value. It is not added to the preview JSON input.

## Column Interpretation

| Column | Source | Interpretation |
|---|---|---|
| `row_no` | Derived from input record position | One-based display number; not a rank or score |
| `candidate_id` | Preview record | Existing candidate identifier |
| `candidate_cell_mgrs` | Preview record | User-facing candidate coordinate |
| `color_class` | Preview record | Existing candidate color classification value |
| `color_name` | Preview record | Existing display color name |
| `overall_score` | Preview record | Existing score displayed without recalculation |
| `shielding_stability_score` | Preview record | Existing component score displayed without recalculation |
| `source_zone` | Preview record | Terrain-source interpretation category |
| `source_sensitive` | Preview record | Boolean interpretation flag |
| `source_zone_reason` | Preview record | Concise interpretation rationale |
| `candidate_reason` | Preview record | Existing candidate explanation text |

The table formatter must not infer new scoring meaning, operational meaning, priority, suitability, or ordering from these columns.

## MGRS External Coordinate Boundary

The user-facing candidate coordinate contract remains:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
```

The table must preserve `candidate_cell_mgrs` and must validate that the preview top-level and record-level external coordinate format remains `MGRS`.

Task 024A and Task 024B do not implement MGRS conversion and do not assess the geographic accuracy of supplied or synthetic placeholder MGRS strings.

## Internal/Debug Coordinate Exclusion

The following internal/debug fields must not appear in table output:

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

A Task 024B formatter should reject preview input containing an internal/debug coordinate key at the top level or within a record. Internal map geometry and raster-processing coordinates remain outside the appendix-table contract.

## Source-Zone Metadata Handling

The table may display:

```text
source_zone
source_sensitive
source_zone_reason
```

These fields are interpretation metadata only. They do not change candidate scoring, LOS/Fresnel values, route scoring, or waypoint scoring.

Displaying `source_sensitive` does not authorize publication of sensitive coordinates or internal coordinate components. The only candidate coordinate shown by default remains `candidate_cell_mgrs`.

## Sorting and Row Numbering Policy

The default policy is:

1. Preserve the order of `preview["records"]`.
2. Assign `row_no` values starting at 1 in that preserved order.
3. Do not sort by candidate ID, color, score, source-zone value, or any other field.
4. Do not perform ranking, rescoring, tie-breaking, or priority assignment.
5. When `max_rows` is supplied, display the first N records in the preserved order and report the omitted count.

A later separate task may propose optional sorting after review. Sorting is not part of the default Task 024B scope.

## Markdown/Text Table Boundary

Task 024B may add one pure Python formatter with a public function such as:

```text
format_preview_appendix_table(preview: Mapping[str, object], *, max_rows: int | None = None) -> str
```

The formatter returns a string only. Markdown pipe-table syntax is recommended because it remains readable as plain text, but implementation should avoid coupling to a Markdown rendering package.

Task 024B does not:

- add a CLI option
- write files
- generate a report
- render a UI table, card, or popup
- render HTML
- alter current preview text or JSON behavior

## File Output Boundary

Task 024B does not add table file output. An operator or later tool may load a JSON file previously produced through `--output-json` and pass the parsed dictionary to the formatter, but file loading and file writing are outside the formatter contract unless a later reviewed task explicitly adds them.

Markdown/table output file storage, path handling, overwrite behavior, encoding, cleanup, and generated-artifact policy remain follow-up concerns.

## Non-Goals

Task 024A includes:

- no source code changes
- no test changes
- no CLI option changes
- no JSON schema changes
- no preview output behavior changes
- no formatter implementation
- no report generation implementation
- no UI/table/card/popup rendering implementation
- no HTML rendering
- no real DEM/DSM/landcover access
- no `METADATA_MAP` access
- no GIS dependencies
- no MGRS conversion
- no MGRS geographic accuracy assessment
- no candidate scoring, LOS/Fresnel, route, or waypoint changes
- no vehicle-control or autopilot output
- no generated Markdown, JSON, TXT, CSV, PDF, image, or diagram files committed

## Task 024B Local Implementation Scope

Task 024B should be limited to a pure Python formatter and focused tests:

1. Add `src/uav_rf_terrain/preview_appendix_table.py`.
2. Add `tests/test_preview_appendix_table.py`.
3. Expose `format_preview_appendix_table(...)` or an equivalently narrow public function.
4. Accept an in-memory mapping that follows the existing preview JSON contract.
5. Validate required top-level and record fields.
6. Preserve the JSON record order.
7. Add one-based `row_no` values only in the returned table string.
8. Format the recommended columns.
9. Support optional positive `max_rows` and a deterministic omitted-row line.
10. Preserve MGRS and source-zone metadata.
11. Reject internal/debug coordinate fields.
12. Return a string only.
13. Do not change `preview_cli.py`, `candidate_display_preview.py`, or existing output contracts.
14. Do not add file output, CLI options, report generation, UI rendering, or terrain integration.

## Acceptance Criteria for Task 024B

Task 024B is acceptable when:

- the formatter accepts a valid reviewed preview dictionary
- required top-level and record fields are validated
- the table contains the recommended columns
- record order is preserved
- `row_no` begins at 1 and is display-only
- score values are formatted from input without recalculation
- `candidate_cell_mgrs` remains the only candidate coordinate column
- `external_coordinate_format` remains `MGRS`
- source-zone metadata is displayed as interpretation metadata
- internal/debug coordinate keys are rejected and absent from output
- `max_rows` accepts only a positive integer or `None`
- omitted-row behavior is deterministic
- the formatter returns a string and creates no file
- no CLI, JSON schema, preview behavior, terrain, scoring, route, waypoint, report, or UI change is introduced
- focused tests and repository verification complete successfully in the Local environment

## Follow-Up Tasks

1. Task 024B-Local: implement the pure Python preview appendix table formatter and focused tests.
2. A later task may add optional table-file output after path and generated-artifact policies are reviewed.
3. A later report task may incorporate a reviewed table string into a paper appendix.
4. A later UI task may consume the JSON-ready record list independently.
5. Real-terrain integration remains a separate reviewed task.
