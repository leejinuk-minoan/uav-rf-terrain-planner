# Preview Table Output Surface Plan

## Purpose

This document defines the planned CLI and explicit file-output surface for the existing preview appendix-table formatter before any CLI implementation begins.

Task 025A is documentation-only. It preserves the current synthetic preview CLI, preview JSON contract, plain-text preview behavior, appendix-table formatter behavior, file-output rules, terrain boundaries, and scoring boundaries.

## Current State

The current implementation has two separate layers:

1. `preview_cli.py` exposes the existing synthetic preview path through stdout and explicit JSON/text files.
2. `preview_appendix_table.py` converts a reviewed preview dictionary into a deterministic Markdown/plain-text table string.

Current facts:

- `preview_cli.py` invokes the synthetic preview path.
- Existing stdout modes are the default plain-text preview and JSON stdout through `--json`.
- Existing explicit file modes are `--output-json PATH` and `--output-text PATH`.
- Existing overwrite opt-in is `--force`.
- Task 024B added `format_preview_appendix_table(preview, max_rows=None) -> str`.
- The formatter is not connected to the CLI.
- The formatter does not read or write files.
- The formatter preserves input record order and derives display-only row numbers.
- No current command produces the appendix-table string.

## Existing CLI Output Modes

| Mode | Command | Destination | Row-limit behavior | Current status |
|---|---|---|---|---|
| Plain-text preview stdout | `python -m uav_rf_terrain.preview_cli --synthetic` | stdout | All rows | Implemented |
| Limited plain-text preview stdout | `python -m uav_rf_terrain.preview_cli --synthetic --max-records 3` | stdout | Limits visible preview rows | Implemented |
| JSON stdout | `python -m uav_rf_terrain.preview_cli --synthetic --json` | stdout | `--max-records` does not truncate JSON | Implemented |
| JSON file | `python -m uav_rf_terrain.preview_cli --synthetic --output-json PATH` | Explicit UTF-8 file | Complete JSON dictionary | Implemented |
| Plain-text preview file | `python -m uav_rf_terrain.preview_cli --synthetic --output-text PATH` | Explicit UTF-8 file | Limits visible preview rows | Implemented |
| Forced JSON overwrite | `python -m uav_rf_terrain.preview_cli --synthetic --output-json PATH --force` | Explicit UTF-8 file | Complete JSON dictionary | Implemented |
| Forced text overwrite | `python -m uav_rf_terrain.preview_cli --synthetic --output-text PATH --force` | Explicit UTF-8 file | Limits visible preview rows | Implemented |

The default command remains the existing plain-text preview stdout mode. Task 025B must not change the behavior, content, status codes, or file policy of these commands.

## Formatter Capability

The Task 024B formatter does:

- accept the reviewed preview dictionary
- validate required preview and record fields
- enforce `external_coordinate_format = MGRS`
- preserve preview record order
- derive one-based display-only `row_no`
- display existing score values without recalculation
- display source-zone interpretation metadata
- normalize line breaks and escape Markdown pipe characters
- support positive `max_rows`
- add a deterministic omitted-row line
- return a Markdown/plain-text table string

The formatter does not:

- parse CLI arguments
- read JSON files
- write files
- create directories
- choose output paths
- load terrain data
- convert MGRS coordinates
- assess MGRS geographic accuracy
- recalculate scores
- sort or rank candidates
- generate a report
- render a UI or HTML surface

## Proposed Output Surface

Task 025B should evaluate and implement only the following minimal options:

```text
--table
--output-table PATH
```

Proposed meanings:

- `--table`: format the existing synthetic `preview_dict` and print the appendix-table string to stdout.
- `--output-table PATH`: format the existing synthetic `preview_dict` and write the table string to one explicit UTF-8 text path.
- `--max-records N`: reuse the existing positive integer as the visible-row limit for both the current plain-text preview and the new table projection. For table modes, pass the value to the formatter as `max_rows`.
- `--force`: reuse the existing overwrite opt-in for `--output-table` in the same way it is used by current explicit file modes.

These names are the reviewed candidates for Task 025B. Task 025A does not add the options or alter the parser.

The proposed surface must consume the already-built in-memory `preview_dict`. It must not add JSON-file input, report generation, UI behavior, or terrain access.

## CLI Mode Conflict Policy

The output selector policy should be simple: at most one output selector may be active.

Output selectors are:

```text
--json
--table
--output-json PATH
--output-text PATH
--output-table PATH
```

Required conflict rules for Task 025B:

- `--json` and `--table` cannot be used together.
- `--json` cannot be combined with any explicit file-output mode.
- `--table` cannot be combined with `--output-json`, `--output-text`, or `--output-table`.
- `--output-table` cannot be combined with `--json`, `--table`, `--output-json`, or `--output-text`.
- `--output-json`, `--output-text`, and `--output-table` are mutually exclusive.
- When no output selector is supplied, the existing plain-text preview stdout remains the default.
- Existing valid commands remain valid and retain their current behavior.
- Mode conflicts are parser/argument errors rather than formatter or file errors.

`--force` is not an output selector. It is meaningful only when an explicit file-output option is selected. Task 025B should preserve current handling outside file modes rather than introduce an unrelated compatibility change.

`--max-records` is also not an output selector. It limits the current plain-text preview and proposed table modes, while JSON modes continue to retain all records.

## File Output Policy

If Task 025B adds `--output-table PATH`, it must reuse the current explicit file-output policy:

- write only to the user-selected explicit path
- do not create parent directories automatically
- fail when the parent directory does not exist
- fail when the target is a directory
- preserve an existing file when `--force` is absent
- allow overwrite when `--force` is supplied
- use UTF-8 text
- normalize output to one trailing newline
- create no additional file
- print a short save confirmation to stdout on success
- do not print the table body to stdout after successful file output
- use `tmp_path` or another temporary directory in tests and local smoke work
- do not commit generated table output

The existing `_write_text_output(...)` path is the preferred reusable policy boundary. Task 025B should avoid introducing a second, inconsistent path-validation or text-writing implementation.

## Status Code Policy

The existing deterministic status-code contract remains:

| Status | Meaning | Proposed table-mode use |
|---:|---|---|
| 0 | Success | Table stdout or explicit table file completes |
| 1 | Handled preview or formatter error | Synthetic preview generation or appendix-table formatting fails with a handled error |
| 2 | Parser or argument error | Invalid arguments or conflicting output selectors |
| 3 | Handled file-output error | Missing parent, directory target, protected existing file, or another handled write error |

Task 025B should handle `PreviewAppendixTableError` as status 1 with concise stderr and no traceback.

Mode conflicts remain status 2. Explicit path and write problems remain status 3. Existing status meanings and existing command behavior must not change.

## MGRS External Coordinate Boundary

The table stdout and table file contract remains:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
```

The only candidate coordinate column in the table is `candidate_cell_mgrs`.

Task 025A and Task 025B do not implement MGRS conversion and do not assess the geographic accuracy of supplied or synthetic placeholder MGRS strings.

## Internal/Debug Coordinate Exclusion

The following internal/debug coordinate fields must not appear in table stdout or table file output:

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

The existing formatter already rejects these keys at the preview top level and record level. Task 025B should preserve that guardrail and add CLI-level regression assertions that no internal/debug coordinate token is emitted.

## Source-Zone Metadata Handling

The table may display:

```text
source_zone
source_sensitive
source_zone_reason
```

These values remain interpretation metadata only.

They do not change candidate scores, LOS/Fresnel values, route values, waypoint values, candidate ordering, row numbering, or color values. Their presence in a table does not create a rank or priority meaning.

## Generated Artifact Policy

Generated table artifacts are runtime outputs, not repository source files.

Required policy:

- local or CI tests create table files only under `tmp_path` or another temporary directory
- local smoke work uses a temporary or explicitly disposable path
- generated Markdown, TXT, JSON, CSV, PDF, image, or report output is not committed
- no example table-output file is added under `docs/`
- no long generated table is pasted into README
- smoke artifacts are removed or left only in managed temporary directories
- CI must not upload table outputs as artifacts without a separately reviewed task

## Non-Goals

Task 025A includes:

- no source code changes
- no test changes
- no CLI option implementation
- no table file-output implementation
- no formatter behavior changes
- no JSON schema changes
- no preview field changes
- no existing CLI behavior changes
- no report generation
- no UI table, card, popup, or map rendering
- no HTML rendering
- no real DEM, DSM, or landcover access
- no `METADATA_MAP` access
- no GIS dependencies
- no MGRS conversion
- no MGRS geographic accuracy assessment
- no candidate scoring changes
- no LOS/Fresnel recalculation
- no route or waypoint scoring changes
- no generated table or report artifact committed
- no external execution-system integration or automated-control output

## Task 025B Local Implementation Scope

Task 025B should be limited to connecting the existing formatter to the existing synthetic preview CLI:

1. Modify `src/uav_rf_terrain/preview_cli.py` only as needed.
2. Import `format_preview_appendix_table` and `PreviewAppendixTableError`.
3. Add `--table` as a boolean stdout selector.
4. Add `--output-table PATH` as one explicit file selector.
5. Extend the output-selector conflict validation without changing current valid commands.
6. Build the synthetic preview once through the existing helper.
7. Use `result.preview_dict` as formatter input.
8. Pass `args.max_records` to the formatter as `max_rows` in table modes.
9. Print the returned table string in `--table` mode.
10. Reuse the existing text-output helper for `--output-table`.
11. Reuse `--force` for table-file overwrite.
12. Map handled formatter errors to status 1.
13. Preserve status 2 for argument conflicts.
14. Preserve status 3 for file-output problems.
15. Keep default plain text, JSON stdout, JSON file, and text file behavior unchanged.
16. Add focused tests, preferably in `tests/test_preview_table_cli_output.py` with only necessary additions to existing CLI tests.
17. Create no generated repository artifact.

Task 025B must not add JSON-file input, report generation, UI rendering, HTML output, terrain integration, coordinate conversion, sorting, ranking, or score recalculation.

## Acceptance Criteria for Task 025B

Task 025B is acceptable when:

- `--table` prints the formatter output to stdout and returns status 0
- `--output-table PATH` writes the same semantic table text to one explicit UTF-8 path and returns status 0
- successful table file output prints only a save confirmation to stdout
- `--max-records N` limits table rows through formatter `max_rows`
- the formatter omission line is preserved
- `--force` protects and overwrites table files under the existing policy
- missing parent and directory targets return status 3
- all output-selector conflicts return status 2 with concise stderr
- formatter validation errors return status 1 with concise stderr
- default plain-text preview behavior is unchanged
- JSON stdout and JSON file remain complete under `--max-records`
- existing plain-text file behavior is unchanged
- table stdout and file output preserve `candidate_cell_mgrs` and MGRS
- internal/debug coordinate tokens remain absent
- source-zone fields remain interpretation metadata
- no source other than the narrow CLI integration is changed without a documented need
- focused tests and all existing CLI/formatter tests pass locally
- compileall, pytest, Ruff, mypy, diff checks, and GitHub Actions complete successfully
- no generated output file is committed

## Follow-Up Tasks

1. Task 025B-Local: implement the minimal table stdout and explicit table-file CLI surface.
2. A later task may add JSON-file input only after input-path and schema-error policies are reviewed.
3. A separate report task may consume the table string without changing the CLI contract.
4. A separate UI task may consume the preview dictionary or records directly.
5. Real-terrain integration remains a separate reviewed task.
