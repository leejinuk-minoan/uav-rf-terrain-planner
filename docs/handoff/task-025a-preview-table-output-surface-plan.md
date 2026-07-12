# Task 025A Preview Table Output Surface Plan

## Purpose

Task 025A documents the planned CLI and explicit file-output surface for the existing preview appendix-table formatter before the formatter is connected to the CLI.

This is a documentation-only task. It preserves all existing preview CLI, JSON, text, formatter, terrain, scoring, route, waypoint, report, and UI behavior.

## Documents Added

- `docs/architecture/preview-table-output-surface-plan.md`
- `docs/prompts/local-task-025b-preview-table-cli-output.md`
- `docs/handoff/task-025a-preview-table-output-surface-plan.md`
- `docs/paper/experiments/EXP-20260712-029-preview-table-output-surface-plan.md`

README receives one short Task 025A summary, and the experiment index receives one EXP-20260712-029 entry.

## Current State

The current synthetic preview CLI supports:

- default plain-text preview stdout
- limited plain-text preview stdout through `--max-records`
- JSON stdout through `--json`
- explicit JSON file output through `--output-json PATH`
- explicit plain-text preview file output through `--output-text PATH`
- overwrite opt-in through `--force`

Task 024B added `format_preview_appendix_table(preview, max_rows=None) -> str`.

The formatter validates the reviewed preview dictionary, preserves record order, derives one-based display row numbers, displays MGRS and source-zone metadata, supports row limiting, and returns a deterministic string. It is not currently connected to the CLI and does not write files.

## Proposed Output Surface

Task 025B should add only:

```text
--table
--output-table PATH
```

Proposed behavior:

- `--table` prints the existing formatter result to stdout.
- `--output-table PATH` writes the formatter result to one explicit UTF-8 path.
- `--max-records N` is reused as formatter `max_rows=N` in table modes.
- `--force` is reused for `--output-table` overwrite.
- existing commands remain unchanged.
- default mode remains the current plain-text preview stdout.

## Mode Conflict Policy

The following are mutually exclusive output selectors:

```text
--json
--table
--output-json PATH
--output-text PATH
--output-table PATH
```

At most one may be active. Conflicts are parser/argument errors with status 2.

`--max-records` and `--force` are not output selectors. JSON modes remain complete under `--max-records`; table modes and existing plain-text modes use it as a visible-row limit.

## File Output Policy

The planned `--output-table` mode reuses the current explicit file policy:

- explicit user-selected path only
- no automatic parent-directory creation
- missing parent fails
- directory target fails
- existing file is preserved without `--force`
- `--force` permits overwrite
- UTF-8 text
- one trailing newline
- save confirmation only on stdout after success
- no generated table file committed
- tests and smoke use temporary paths

The existing text-output helper is the preferred implementation boundary.

## Status Code Policy

The current meanings remain:

```text
0 = success
1 = handled preview or formatter error
2 = parser or argument error
3 = handled file-output error
```

A handled `PreviewAppendixTableError` should return status 1. Mode conflicts return status 2. Path and write failures return status 3.

## MGRS External Coordinate Handling

Table stdout and table files preserve:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
```

The table contains no other candidate coordinate column. This task does not add coordinate conversion or geographic-accuracy assessment.

## Internal/Debug Coordinate Handling

The following remain excluded:

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

The existing formatter rejects these keys. Task 025B should add CLI-level assertions that the corresponding tokens remain absent from table stdout and files.

## Source-Zone Metadata Handling

The table may display:

```text
source_zone
source_sensitive
source_zone_reason
```

They remain interpretation metadata. They do not affect score, order, rank, color, route, or waypoint values.

## Recommended Task 025B Scope

Task 025B-Local should:

- modify `src/uav_rf_terrain/preview_cli.py` only as necessary
- add `--table`
- add `--output-table PATH`
- reuse `result.preview_dict`
- call the existing formatter
- reuse `--max-records` as table `max_rows`
- reuse the existing text writer and `--force`
- extend mode-conflict validation
- preserve status codes 0 through 3
- preserve every current valid command
- add focused tests, preferably in `tests/test_preview_table_cli_output.py`
- use temporary paths and commit no generated output

It must not add JSON-file input, report generation, UI or HTML rendering, terrain access, coordinate conversion, sorting, ranking, or score recalculation.

## Test/CI Result

Task 025A changes no source or test code. The Cloud Agent does not claim local compile, pytest, Ruff, mypy, or CLI execution. GitHub Actions is checked after PR creation and rechecked on the final documentation head.

## Overall Status

The table formatter now has a bounded future CLI surface with explicit mode-conflict, file-output, status-code, coordinate, metadata, and generated-artifact policies. The next Local task can implement the connection without redefining the formatter or existing CLI behavior.

## Limitations

Task 025A does not:

- implement or execute new CLI options
- change source or tests
- change formatter behavior
- change JSON or existing plain-text output
- write a table file
- generate a report
- render UI, HTML, map, card, or popup content
- access terrain data or `METADATA_MAP`
- add GIS dependencies
- convert MGRS coordinates
- assess MGRS geographic accuracy
- change scoring, LOS/Fresnel, route, or waypoint logic
- add external execution-system integration or automated-control output

## Public Repository Sensitivity Check

Only Markdown documentation and index updates are included. No private absolute path, sensitive coordinate, credential, token, secret, terrain raster, `METADATA_MAP` file, GIS file, generated table, generated report, JSON/TXT/CSV/PDF/image output, QGIS project, or archive is included.

## Follow-Up Tasks

1. Task 025B-Local: implement `--table` and `--output-table PATH` with focused tests.
2. A later task may add JSON-file input after a separate input-path and schema-error review.
3. A separate report task may consume the table string.
4. A separate UI task may consume the preview dictionary directly.
5. Real-terrain integration remains a separate reviewed task.
