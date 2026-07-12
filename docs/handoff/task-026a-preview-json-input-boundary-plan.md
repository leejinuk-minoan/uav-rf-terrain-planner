# Task 026A Preview JSON Input Boundary Plan

## Purpose

Task 026A documents the boundary for reading a saved preview JSON file and using it only as input to the existing table stdout or explicit table-file surfaces.

This is a documentation-only task. It preserves current synthetic commands, output contracts, formatter behavior, terrain/scoring boundaries, and repository data restrictions.

## Documents Added

- `docs/architecture/preview-json-input-boundary-plan.md`
- `docs/prompts/local-task-026b-preview-json-input-table-output.md`
- `docs/handoff/task-026a-preview-json-input-boundary-plan.md`
- `docs/paper/experiments/EXP-20260712-031-preview-json-input-boundary-plan.md`

README receives one Task 026A sentence and the experiment index receives one EXP-20260712-031 entry.

## Current State

- `preview_cli.py` requires `--synthetic`.
- Synthetic preview data can be printed or saved through existing plain-text, JSON, and appendix-table modes.
- `--output-json PATH` can save the reviewed preview dictionary.
- `--table` and `--output-table PATH` consume the synthetic in-memory preview dictionary.
- No CLI option reads a saved preview JSON file.
- `format_preview_appendix_table(...)` already validates the preview contract and returns a deterministic table string.

## Proposed Input Source Surface

Task 026B should add only:

```text
--input-json PATH
```

The option reads one explicit UTF-8 JSON file, requires a top-level object, and passes the decoded mapping to the existing formatter. It is not implemented in Task 026A.

## Source Selector Policy

The future source selectors are:

```text
--synthetic
--input-json PATH
```

Exactly one is required. Missing or conflicting sources are status-2 argument errors. Existing synthetic commands remain unchanged, and saved-input mode must not invoke synthetic generation.

## Output Compatibility

For saved input, Task 026B supports only:

```text
--input-json PATH --table
--input-json PATH --output-table PATH
```

`--max-records N` becomes table `max_rows=N`, and `--force` applies only to table-file overwrite.

Saved input is not connected to default plain-text preview, `--json`, `--output-json`, or `--output-text` in Task 026B. Unsupported combinations return status 2.

## Input File Policy

- explicit path only;
- no default discovery or application glob expansion;
- path must exist and be a file;
- directories fail;
- UTF-8 JSON only;
- top level must be an object/mapping;
- input remains unchanged;
- tests use temporary paths;
- no terrain or `METADATA_MAP` access;
- no generated JSON input is committed.

## JSON Decode and Schema Error Policy

Handled status-1 errors include missing, directory, unreadable, invalid-UTF-8, invalid-JSON, non-object input, missing fields, invalid types, invalid MGRS contract, internal coordinates, record-count mismatch, and other formatter contract failures.

Failures use concise stderr without traceback, print no partial table, and create or replace no output file.

## Status Code Policy

```text
0 = success
1 = handled preview/input/formatter error
2 = parser / argument error
3 = handled output-file error
```

Input problems remain status 1. Source/output conflicts remain status 2. Status 3 remains reserved for output path or write failures.

## MGRS External Coordinate Handling

Saved input and table output preserve:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
```

No coordinate conversion or geographic-accuracy assessment is added. The table continues to show only `candidate_cell_mgrs` as the candidate coordinate column.

## Internal/Debug Coordinate Handling

The existing formatter rejects:

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

Rejected saved input returns status 1 and produces no partial stdout or output file.

## Source-Zone Metadata Handling

The existing fields remain interpretation metadata:

```text
source_zone
source_sensitive
source_zone_reason
```

They do not alter score, order, rank, color, LOS/Fresnel, route, or waypoint values.

## Recommended Task 026B Scope

Task 026B should minimally modify `src/uav_rf_terrain/preview_cli.py`, add focused tests in `tests/test_preview_json_input_table_output.py`, reuse the existing formatter/text writer, preserve existing synthetic modes, and add concise handoff/experiment records.

It should not add JSON copying, plain-text reconstruction from saved JSON, report generation, UI/HTML, terrain access, coordinate conversion, sorting, ranking, or score recalculation.

## Test/CI Result

Task 026A changes no source or test code. The Cloud Agent does not claim local compile, pytest, Ruff, mypy, CLI, formatter, or file-I/O execution. GitHub Actions is checked after PR creation on the final documentation head.

## Overall Status

The saved preview JSON input path now has a bounded source-selector, output-compatibility, input-file, error, status-code, coordinate, metadata, and artifact policy. Task 026B can implement the narrow connection without redefining the preview or table contracts.

## Limitations

Task 026A does not implement or execute JSON input, change source/tests, alter formatter/schema/output behavior, generate files, access terrain data, convert coordinates, or render report/UI/HTML content.

## Public Repository Sensitivity Check

Only Markdown documentation and index updates are included. No private path, sensitive coordinate, credential, token, secret, terrain raster, `METADATA_MAP` file, GIS file, generated JSON/table/report, CSV, PDF, image, QGIS project, or archive is included.

## Follow-Up Tasks

1. Task 026B-Local: implement `--input-json PATH` for table stdout and explicit table-file output.
2. A later task may define plain-text reconstruction from structured JSON.
3. Separate report and UI tasks may consume reviewed preview data.
4. Real-terrain integration remains separate.
