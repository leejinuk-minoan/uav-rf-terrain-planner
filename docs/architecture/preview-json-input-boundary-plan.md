# Preview JSON Input Boundary Plan

## Purpose

This document defines the boundary for using a previously saved preview JSON file as input to the existing appendix-table formatter and table CLI surfaces.

Task 026A is documentation-only. It does not add a CLI option, read a JSON file, change the preview schema, change formatter behavior, or alter existing synthetic commands.

## Current State

- `preview_cli.py` currently requires `--synthetic`.
- `--table` prints an appendix table from the synthetic preview dictionary.
- `--output-table PATH` writes appendix-table text from the synthetic preview dictionary.
- `--output-json PATH` can save the reviewed preview JSON dictionary.
- No current CLI path reads a saved preview JSON file.
- `format_preview_appendix_table(preview, max_rows=None)` validates the preview dictionary and returns a deterministic table string.
- The formatter does not read or write files.

Task 026A defines input-source, path, error, status, coordinate, and follow-up implementation boundaries. It does not implement JSON input.

## Existing Source and Output Model

The current source selector is:

```text
--synthetic
```

Current output selectors are:

```text
--json
--table
--output-json PATH
--output-text PATH
--output-table PATH
```

At most one output selector may be active. With `--synthetic` and no output selector, the existing plain-text preview stdout remains the default.

```text
--synthetic
→ build_synthetic_candidate_preview_smoke(...)
→ preview_dict / preview_text
→ one selected stdout or explicit file projection
```

## Proposed Input Source Surface

Task 026B should evaluate and implement one minimal input option:

```text
--input-json PATH
```

Meaning:

- read one explicitly selected UTF-8 JSON file;
- require a JSON object/mapping at the top level;
- treat the decoded object as the existing preview dictionary contract;
- pass the mapping to `format_preview_appendix_table(...)` for contract validation;
- support this source only for table stdout or explicit table-file output in Task 026B.

The proposed source is saved preview data. It is not a terrain source, report generator, UI source, route source, or coordinate-conversion path.

Task 026A does not add the option to the parser.

## Source Selector Policy

Task 026B should define:

```text
--synthetic
--input-json PATH
```

Policy:

- exactly one source selector is required;
- `--synthetic` and `--input-json PATH` cannot be used together;
- no source selector is a parser/argument error;
- conflicting source selectors are a parser/argument error;
- existing `--synthetic` commands remain valid and unchanged;
- `--input-json PATH` must not invoke synthetic preview generation;
- source selection is checked before input reading or output generation.

The current parser-level `required=True` for `--synthetic` may be replaced by explicit exactly-one-source validation in Task 026B, while preserving every existing synthetic command.

## Output Selector Compatibility

Task 026B should connect saved preview JSON only to the existing table projection.

Allowed:

```text
--input-json PATH --table
--input-json PATH --output-table PATH
```

Allowed modifiers:

```text
--max-records N
--force
```

- `--max-records N` becomes formatter `max_rows=N` in table modes.
- `--force` affects only explicit output-file overwrite.

Not included in Task 026B:

```text
--input-json PATH --json
--input-json PATH --output-json PATH
--input-json PATH --output-text PATH
--input-json PATH
```

A saved preview JSON object does not contain the current `preview_text` runtime value. Reconstructing that text requires a separate formatter boundary. Re-emitting or copying JSON also expands the task without adding the intended table-consumer path.

Output policy remains:

- at most one output selector may be active;
- saved input requires `--table` or `--output-table PATH`;
- unsupported saved-input output combinations are status-2 parser/argument errors;
- synthetic output modes remain unchanged.

## Input File Policy

`--input-json PATH` should follow this policy:

- explicit user-selected input path only;
- no default path, path discovery, or application-level glob expansion;
- path must exist and identify a file, not a directory;
- read UTF-8 text and decode standard JSON;
- require a top-level object/mapping;
- do not mutate, create, replace, or delete the input file;
- no real DEM, DSM, landcover, or `METADATA_MAP` access;
- tests use `tmp_path` or another managed temporary directory;
- no generated or copied preview JSON file is committed.

Input-path checks are separate from output-path checks. Input problems are not status-3 output failures.

A narrow helper such as `_read_preview_json(path: Path) -> dict[str, object]` may handle path, read, decode, and top-level-object checks. It should not duplicate the schema validation already performed by `format_preview_appendix_table(...)`.

## JSON Decode and Schema Error Policy

Handled preview-input failures include:

- missing input file;
- directory input;
- unreadable input;
- invalid UTF-8;
- invalid JSON;
- non-object JSON top level;
- missing required preview or record fields;
- invalid MGRS contract;
- internal/debug coordinate fields;
- record-count mismatch;
- invalid score or `source_sensitive` types;
- any other documented formatter contract failure.

Required behavior:

- classify read, decode, top-level-object, schema, and formatter failures as handled preview-input errors;
- print concise stderr without a traceback;
- print no partial table;
- create or replace no output file after an input or formatter failure;
- preserve the input file unchanged.

Task 026B may introduce one concise input exception type or normalize standard read/decode errors at the CLI boundary. Raw exception representations should not become a stable output contract.

## Status Code Policy

Existing meanings remain:

```text
0 = success
1 = handled preview/input/formatter error
2 = parser / argument error
3 = handled output-file error
```

| Situation | Status |
|---|---:|
| Table stdout or table file completes | 0 |
| Synthetic preview generation fails in a handled path | 1 |
| Input read, UTF-8 decode, JSON decode, top-level-object, schema, or formatter validation fails | 1 |
| Source selector is missing or conflicting | 2 |
| Output selector conflicts or saved-input output is unsupported | 2 |
| Output parent is missing, output target is a directory, protected output exists, or output write fails | 3 |

Status 3 is reserved for selected output paths and output writes. Existing synthetic command status behavior must not change.

## MGRS External Coordinate Boundary

Saved preview JSON retains:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
```

Task 026B must use formatter validation for the top-level and record-level MGRS contract, display only `candidate_cell_mgrs` as the candidate coordinate column, perform no coordinate conversion, and make no geographic-accuracy assessment of supplied MGRS text.

## Internal/Debug Coordinate Exclusion

The following fields remain outside saved preview input and table output:

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

The formatter rejects these keys at the preview top level or record level. Rejection must produce a concise status-1 error, no partial table, and no created or replaced output file.

## Source-Zone Metadata Handling

Saved preview JSON may preserve:

```text
source_zone
source_sensitive
source_zone_reason
```

These fields remain interpretation metadata only. Reading them from a file does not change scores, ordering, row numbering, colors, LOS/Fresnel values, route values, or waypoint values, and does not create a priority or ranking meaning.

## Generated Artifact Policy

- Tests may create temporary JSON input and table-output files under `tmp_path`.
- Local smoke work uses temporary or explicitly disposable paths.
- Generated JSON, TXT, Markdown, CSV, PDF, image, or report outputs are not committed.
- No sample preview JSON or output table file is added under `docs/`.
- README does not contain a long generated JSON payload or table.
- CI does not upload generated input or output files in this task family.
- No Git LFS, package upload, release-asset upload, or large-data download is introduced.

## Non-Goals

Task 026A includes:

- no source or test changes;
- no CLI option or JSON-input implementation;
- no formatter behavior or JSON schema change;
- no preview field or existing synthetic CLI behavior change;
- no output-file behavior change;
- no report generation or UI/map/card/popup/HTML rendering;
- no real terrain or `METADATA_MAP` access;
- no GIS dependency;
- no MGRS conversion or geographic-accuracy assessment;
- no scoring, LOS/Fresnel, route, or waypoint change;
- no generated input, output, or report artifact;
- no external execution-system integration or automated vehicle output.

## Task 026B Local Implementation Scope

Task 026B should be limited to:

1. minimally modify `src/uav_rf_terrain/preview_cli.py`;
2. add `--input-json PATH`;
3. replace parser-level `--synthetic` requirement with exactly-one-source validation;
4. preserve all existing synthetic commands;
5. permit saved input only with `--table` or `--output-table PATH`;
6. read UTF-8 JSON and require a top-level mapping;
7. pass the mapping directly to `format_preview_appendix_table(...)`;
8. pass `--max-records` as `max_rows`;
9. reuse `_write_text_output(...)` and `--force` for table files;
10. avoid calling the synthetic helper for saved input;
11. normalize input/read/decode/schema/formatter failures to status 1;
12. preserve status 2 for argument errors and status 3 for output errors;
13. emit no partial table and create no output file on input or formatter failure;
14. add focused tests, preferably `tests/test_preview_json_input_table_output.py`;
15. make only necessary additions to existing CLI tests;
16. add concise Task 026B handoff and experiment records;
17. commit no generated input or output artifact.

Task 026B must not add default input discovery, JSON copying, plain-text reconstruction from JSON, report generation, UI/HTML rendering, terrain integration, coordinate conversion, sorting, ranking, or score recalculation.

## Acceptance Criteria for Task 026B

Task 026B is acceptable when:

- valid `--input-json PATH --table` and `--output-table PATH` paths work with status 0;
- exactly one source selector is required;
- missing or conflicting source selectors return status 2;
- unsupported saved-input output combinations return status 2;
- all existing synthetic commands retain behavior;
- saved input does not invoke synthetic preview generation;
- decoded mappings are not mutated;
- `--max-records` limits table rows and preserves the omission line;
- `--force` reuses existing output protection;
- missing, directory, unreadable, invalid-UTF-8, invalid-JSON, and non-object inputs return status 1;
- schema, field-type, MGRS, internal-coordinate, and record-count failures return status 1;
- input or formatter failures emit no partial table and create or replace no output file;
- output path/write problems remain status 3;
- table output preserves MGRS and source-zone interpretation metadata;
- internal/debug coordinate tokens remain absent;
- no preview schema, formatter, terrain, scoring, route, waypoint, report, or UI behavior changes;
- focused and existing tests plus compileall, Ruff, mypy, diff checks, and GitHub Actions complete successfully;
- no generated input or output file is committed.

## Follow-Up Tasks

1. Task 026B-Local: implement saved preview JSON input for table stdout and explicit table-file output.
2. A later task may define reconstruction of human-readable preview text from structured JSON.
3. Separate report and UI tasks may consume reviewed preview JSON or table strings.
4. Real-terrain integration remains a separate reviewed task.
