# Preview Report CLI Output Boundary Plan

## Purpose

This document defines the boundary for a later Local task that may connect the existing pure `format_preview_report(...)` formatter to report stdout and explicit report-file output in the preview CLI.

Task 030A is planning and documentation only. It changes no source code, tests, CLI options, formatter behavior, preview JSON schema, preview fields, or file-output behavior.

The goal is to fix source/output compatibility, argument validation, status-code handling, newline behavior, and artifact policy before `--report` or `--output-report PATH` is implemented.

## Current Implemented State

Current source selectors are:

```text
--synthetic
--input-json PATH
```

Current output selectors are:

```text
--json
--table
--output-json PATH
--output-text PATH
--output-table PATH
```

The current pure report boundary is:

```python
format_preview_report(
    preview: Mapping[str, object],
    *,
    include_table: bool = True,
) -> str
```

The handled formatter exception is:

```text
PreviewReportError
```

The formatter validates through the existing appendix-table boundary, preserves existing candidate order and values, includes the appendix table by default, performs no file I/O, and returns a report string with exactly one trailing newline.

The current CLI does not implement:

```text
--report
--output-report PATH
```

## Proposed CLI Surface

Task 030B may add two output selectors:

```text
--report
--output-report PATH
```

Proposed policy:

- `--report` prints the report string to stdout;
- `--output-report PATH` writes the report string to one explicit UTF-8 path;
- both are output selectors and therefore conflict with every other output selector;
- the existing synthetic default plain-text stdout behavior remains unchanged;
- `--output-text` remains the existing plain preview-text file mode and is not repurposed;
- `--output-report` is a distinct report-file mode;
- `--force` reuses the current explicit file overwrite policy;
- `--max-records` is not applied to reports and must be rejected with report output as a parser/argument error;
- report generation calls `format_preview_report(preview_dict)` with its default `include_table=True`;
- Task 030B adds no CLI option for excluding the appendix table.

The existing behavior of `--force` without an explicit output path is not broadened or otherwise changed by Task 030B.

## Proposed Source and Output Compatibility

Proposed report compatibility:

| Source | `--report` | `--output-report PATH` |
|---|---:|---:|
| `--synthetic` | Allowed | Allowed |
| `--input-json PATH` | Allowed | Allowed |

The complete source policy remains:

- exactly one source selector is required;
- at most one output selector may be active;
- synthetic input with no output selector retains existing plain-text preview stdout;
- saved JSON without a supported table or report selector remains an argument error;
- saved JSON with `--table` or `--output-table PATH` remains supported;
- saved JSON with `--report` or `--output-report PATH` becomes supported;
- saved JSON with `--json`, `--output-json PATH`, or `--output-text PATH` remains unsupported.

Proposed compatibility matrix:

| Source | Default text | JSON stdout | JSON file | Text file | Table stdout | Table file | Report stdout | Report file |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `--synthetic` | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| `--input-json PATH` | No | No | No | No | Yes | Yes | Yes | Yes |

## Proposed Report Stdout Behavior

For `--report`, Task 030B should:

1. resolve the existing source path;
2. build the synthetic preview dictionary or load the selected saved preview JSON object;
3. call `format_preview_report(preview_dict)` exactly once;
4. write the returned report string to stdout;
5. create no file;
6. emit no JSON or table-only output;
7. emit no stderr on success.

The formatter currently returns exactly one trailing newline. The CLI must preserve that contract without adding a second newline. The recommended implementation is equivalent to:

```python
print(report_text, end="")
```

Task 030B tests should assert that report stdout ends with one newline and not two.

## Proposed Report File Output Behavior

For `--output-report PATH`, Task 030B should:

1. resolve and validate the source;
2. build or load the preview dictionary;
3. call `format_preview_report(preview_dict)` exactly once;
4. complete formatter validation before any output-file write;
5. write the report to the explicit path using the existing text-output helper;
6. preserve the existing UTF-8 and one-trailing-newline policy;
7. print the existing confirmation style on success:

```text
preview saved: <PATH>
```

Existing file policy remains:

- no automatic parent-directory creation;
- a missing parent returns status 3;
- a directory target returns status 3;
- an existing target is protected unless `--force` is supplied;
- an output write failure returns status 3;
- invalid input or formatter failure must not create, truncate, or replace the selected report path.

Because `_write_text_output(...)` normalizes text to one trailing newline, the existing helper may be reused without changing its behavior.

## Proposed Formatter Integration

Task 030B may import:

```python
from .preview_report import PreviewReportError, format_preview_report
```

Integration boundary:

- synthetic mode reuses the existing `result.preview_dict`;
- saved-input mode reuses the existing `_read_preview_json(...)` result;
- report generation occurs only after one preview dictionary is available;
- `format_preview_report(preview_dict)` is called once for the selected report output;
- `PreviewReportError` is handled as a formatter/input error with status 1;
- report mode relies on the formatter default `include_table=True`;
- report mode does not call `format_preview_appendix_table(...)` directly;
- report mode does not change the pure formatter implementation or its section contract.

Task 030B should keep table and report variables separate so existing table-only behavior remains unchanged.

## Argument Validation Boundary

Task 030B must preserve and extend the existing parser validation as follows:

- exactly one of `--synthetic` or `--input-json PATH` is required;
- at most one output selector is active;
- `--report` conflicts with `--json`, `--table`, every explicit output path, and `--output-report PATH`;
- `--output-report PATH` conflicts with all existing output selectors;
- saved JSON supports only table stdout, table file, report stdout, or report file;
- bare saved JSON input remains status 2;
- saved JSON with JSON stdout, JSON file, or plain-text file remains status 2;
- `--max-records` with either report selector is status 2;
- the current behavior of `--force` outside explicit file-output modes remains unchanged.

Rejecting `--max-records` avoids a report whose summary covers all records while its embedded table is ambiguously limited. Report row limits require a separate reviewed design.

## Status and Error Boundary

Existing status meanings remain:

```text
0 = success
1 = handled preview/input/formatter error
2 = parser / argument error
3 = handled output-file error
```

Proposed Task 030B mapping:

| Situation | Status |
|---|---:|
| Report stdout or report file completes | 0 |
| Synthetic preview generation fails in a handled path | 1 |
| Saved JSON read, UTF-8 decode, JSON decode, or top-level validation fails | 1 |
| `PreviewReportError` occurs | 1 |
| Source or output selectors conflict | 2 |
| Saved-input output combination is unsupported | 2 |
| Report output is combined with `--max-records` | 2 |
| Output parent is missing | 3 |
| Output target is a directory | 3 |
| Existing output is protected without `--force` | 3 |
| Handled report-file write fails | 3 |

Handled report errors should use concise stderr without a traceback. Recommended formatter-error prefix:

```text
preview report error: <message>
```

Input and formatter validation must finish before report-file writing.

## Coordinate and Metadata Boundary

Report output preserves these user-facing fields and meanings:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
source_zone
source_sensitive
source_zone_reason
```

Task 030B must not add coordinate conversion, geographic-accuracy assessment, or internal/debug coordinate output.

Internal/debug names remain excluded:

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

Report CLI integration must not change candidate scores, colors, record order, rank, routes, or waypoints.

## Source-Zone Metadata Boundary

The following remain interpretation metadata:

```text
source_zone
source_sensitive
source_zone_reason
```

Task 030B may display values already produced by the pure formatter. It must not:

- recalculate scores from source-zone categories;
- exclude candidates because a source-sensitive flag is true;
- alter order or rank based on a source-zone reason;
- convert source metadata into an operational suitability decision;
- represent source metadata as measured real-world link quality.

## Artifact Handling Boundary

Task 030B report-file behavior is limited to one explicit user-selected path.

Policy:

- no default report directory;
- no path discovery;
- no automatic parent creation;
- overwrite only with `--force`;
- tests use `tmp_path` or another managed temporary directory;
- no generated sample report is committed;
- no GitHub Actions artifact upload;
- no Git LFS;
- no package upload;
- no release asset;
- no terrain, raster, QGIS, image, PDF, CSV, JSON, or generated text artifact is added to the repository.

## Task 030B Local Scope

Recommended branch:

```text
agent/task-030b-preview-report-cli-output
```

Recommended changed files:

```text
src/uav_rf_terrain/preview_cli.py
tests/test_preview_report_cli_output.py
docs/handoff/task-030b-preview-report-cli-output.md
docs/paper/experiments/EXP-20260712-039-preview-report-cli-output.md
docs/paper/experiments/README.md
```

Task 030B should:

- add `--report`;
- add `--output-report PATH`;
- integrate the existing pure report formatter;
- support synthetic report stdout and report file;
- support saved JSON report stdout and report file;
- reject report output with `--max-records`;
- preserve existing JSON, text, table, and saved-input behavior;
- preserve existing file protection and `--force` behavior;
- add focused tests;
- change no report formatter behavior, schema, GIS, coordinate, scoring, route, waypoint, or UI behavior.

Task 030A uses:

```text
EXP-20260712-038-preview-report-cli-output-boundary-plan.md
```

Task 030B should use:

```text
EXP-20260712-039-preview-report-cli-output.md
```

## Acceptance Criteria for Task 030B

Task 030B is acceptable when:

1. `--synthetic --report` returns status 0 and report stdout;
2. report stdout ends with exactly one newline;
3. `--synthetic --output-report PATH` writes the report file;
4. `--input-json PATH --report` outputs a report from saved preview JSON;
5. `--input-json PATH --output-report PATH` writes a report file;
6. each report selector conflicts with every other output selector;
7. bare saved JSON input remains rejected;
8. saved JSON with JSON stdout, JSON file, or plain-text file remains rejected;
9. report output with `--max-records` is rejected with status 2;
10. report output contains expected report headings;
11. report output preserves MGRS and `candidate_cell_mgrs` content;
12. internal/debug coordinate fields are not exposed;
13. invalid saved-input report returns status 1;
14. formatter error returns status 1;
15. missing-parent, directory, protected-existing-file, and write failures return status 3;
16. `--force` permits report-file overwrite;
17. invalid input or formatter failure does not create or replace a report file;
18. all existing preview CLI, JSON, text, table, saved-input, and report formatter tests pass;
19. no generated report artifact is committed.

## Non-Goals

Task 030A includes no:

- source-code change;
- test change;
- CLI option implementation;
- report stdout implementation;
- report-file output implementation;
- report formatter behavior change;
- preview JSON schema or field change;
- appendix-table behavior change;
- report row-limit option;
- appendix-table exclusion CLI option;
- HTML, PDF, image, figure, map, widget, card, popup, or interactive rendering;
- real DEM/DSM/landcover or `METADATA_MAP` access;
- GIS dependency change;
- MGRS conversion or geographic validation;
- field RF measurement validation;
- candidate rescoring or reranking;
- LOS/Fresnel recalculation;
- route or waypoint change;
- external-device or flight-control integration;
- generated runtime artifact commit.

## Follow-Up Tasks

1. Task 030B-Local: implement report stdout and explicit report-file output only after this plan is merged.
2. Preserve Task 029B's pure formatter contract while implementing CLI integration.
3. Reconcile current workflow documentation after Task 030B is merged and tested.
4. Keep UI, rendered artifacts, and real-terrain integration in separate reviewed tasks.
