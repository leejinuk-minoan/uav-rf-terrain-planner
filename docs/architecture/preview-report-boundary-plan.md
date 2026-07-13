# Preview Report Boundary Plan

## Purpose

This document defines the boundary for a later Local task that may transform an existing reviewed preview JSON dictionary into a deterministic human-readable Markdown/plain-text report string.

Task 029A is planning and documentation only. It does not change source code, tests, CLI options, formatter behavior, the preview JSON schema, preview fields, or file-output behavior.

The immediate implementation candidate is one pure formatter. CLI integration, report-file writing, HTML, PDF, images, and interactive presentation remain separate reviewed tasks.

## Current Implemented Inputs

The current implemented preview workflow provides these reusable inputs:

```text
preview JSON dictionary
saved preview JSON file
appendix table string
```

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

The CLI currently supports preview JSON and appendix-table workflows. It does not support a report output mode. The only dedicated downstream formatter is `format_preview_appendix_table(...)`; no preview report formatter exists.

A saved preview JSON file is currently accepted only by the CLI table path. A future pure report formatter may receive the already-decoded preview mapping, but Task 029B must not add JSON file reading or CLI behavior.

## Current Implemented Outputs

Current outputs are:

```text
plain-text preview stdout
JSON stdout
explicit JSON file
explicit plain-text file
appendix table stdout
explicit appendix table file
```

The following report selectors do not exist:

```text
--report
--output-report PATH
```

Task 029A does not add them. Task 029B must also leave the CLI unchanged.

## Proposed Report Formatter Boundary

Recommended module:

```text
src/uav_rf_terrain/preview_report.py
```

Recommended public function:

```python
format_preview_report(
    preview: Mapping[str, object],
    *,
    include_table: bool = True,
) -> str
```

Recommended exception:

```python
class PreviewReportError(ValueError):
    ...
```

The formatter should:

- remain pure Python;
- accept an already-decoded preview mapping;
- validate against the existing reviewed preview contract;
- avoid mutating the input mapping or nested records;
- perform no file reading or writing;
- contain no CLI parser or process-status behavior;
- access no GIS, terrain, raster, or map data;
- perform no MGRS conversion or geographic validation;
- perform no score, rank, order, LOS, Fresnel, route, or waypoint recalculation;
- reuse `format_preview_appendix_table(...)` when `include_table=True`;
- return one deterministic Markdown/plain-text string;
- describe the output as a human-review/report draft rather than an operational result.

Task 029B should prefer reuse of the existing appendix-table validation boundary. If a small shared validation helper becomes necessary, it must preserve existing table behavior and remain within the two approved preview formatter modules and their focused tests. A broad refactor is outside scope.

## Proposed Report Sections

Recommended deterministic section order:

```text
# Preview Candidate Report

## Summary
## Source and Output Context
## Candidate Overview
## Source-Zone Interpretation
## Coordinate Boundary
## Appendix Table
## Limitations
```

Section responsibilities:

### Summary

Summarize:

- `record_count`;
- `source_sensitive_count` when present;
- `external_coordinate_format`;
- `user_coordinate_field`;
- the report's review-oriented purpose.

### Source and Output Context

State that the formatter receives a preview mapping. The mapping does not currently encode whether it originated from the synthetic in-memory path or from a saved JSON file. When source provenance is not present, the report should use a deterministic statement such as:

```text
Input provenance: not encoded in preview
```

The formatter must not infer provenance from candidate values or paths.

### Candidate Overview

Summarize without changing the records:

- candidate count;
- color class/name counts in first-seen deterministic order or a documented stable order;
- minimum and maximum existing `overall_score` values;
- minimum and maximum existing `shielding_stability_score` values.

The overview is a projection of existing values. It must not rescore, sort, rerank, exclude, or relabel candidates.

### Source-Zone Interpretation

Explain that:

```text
source_zone
source_sensitive
source_zone_reason
```

are interpretation metadata. They do not alter candidate score, record order, color classification, LOS/Fresnel values, route values, or waypoint values.

The section may summarize source-zone counts and source-sensitive counts from existing fields. It must not convert metadata into a suitability decision.

### Coordinate Boundary

State that the user-facing coordinate boundary is:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
user_coordinate_field = candidate_cell_mgrs
```

The formatter displays existing MGRS text only. It does not convert coordinates or assess geographic correctness.

### Appendix Table

When `include_table=True`, include the exact result of the existing `format_preview_appendix_table(preview)` formatter under this heading.

When `include_table=False`, omit the heading and table together so output remains deterministic and does not imply that a table was generated.

Task 029B does not add row-limit behavior to the report function. Any later report row-limit design requires a separate reviewed boundary because the summary and table must remain internally consistent.

### Limitations

Include concise statements that the report:

- is based on reviewed preview fields only;
- performs no MGRS conversion or geographic validation;
- performs no field RF measurement validation;
- does not recalculate LOS/Fresnel values;
- does not change candidate scoring or ordering;
- does not change route or waypoint results;
- is not a flight-control, vehicle-control, or operational-decision output.

## Input Contract

Task 029B should use the existing preview JSON dictionary contract rather than create a report-specific schema.

Required top-level fields should remain compatible with the existing appendix-table formatter:

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

Required record fields should remain compatible with the existing appendix-table formatter:

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

Policy:

- do not introduce a new preview schema;
- do not add report-only fields to the preview mapping;
- do not rename, remove, or reinterpret existing fields;
- retain `record_count == len(records)` validation;
- retain non-empty record-sequence validation;
- retain MGRS external-format and user-coordinate-field validation;
- retain existing numeric and boolean type checks;
- retain internal/debug coordinate rejection;
- do not require source-file paths or runtime provenance.

The report formatter may catch `PreviewAppendixTableError` and raise `PreviewReportError` with a concise chained message. Invalid input must not leak a partial report string.

## Output Contract

The return type is:

```text
str
```

Output policy:

- deterministic Markdown/plain-text;
- UTF-8-safe content;
- fixed heading order;
- stable summary wording;
- no path argument;
- no file read or write;
- no trailing artifact creation;
- no HTML;
- no image or figure;
- no PDF;
- no map, card, popup, or interactive UI;
- no generated artifact committed to the repository.

The pure formatter may return a string with or without one terminal newline, but Task 029B tests must choose and fix one behavior. CLI/file writers remain responsible for any later external newline normalization.

## Status and Error Boundary

The pure formatter uses exceptions rather than process status codes.

Recommended handled exception:

```text
PreviewReportError
```

Recommended behavior:

- invalid top-level or record structure raises `PreviewReportError`;
- existing appendix-table validation failures are translated to `PreviewReportError` when they cross the report formatter boundary;
- no stderr printing;
- no traceback handling inside the formatter;
- no partial report return on failure.

CLI status mapping is outside Task 029B. The existing CLI meanings remain unchanged:

```text
0 = success
1 = handled preview/input/formatter error
2 = parser / argument error
3 = handled output-file error
```

A separate Task 030A plan and Task 030B Local implementation may review report stdout and report-file status mapping. Task 029A and Task 029B must not modify it.

## Coordinate and Metadata Boundary

User-facing coordinate and metadata fields remain:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
source_zone
source_sensitive
source_zone_reason
```

The formatter must not expose or accept internal/debug coordinate fields as user-facing report values. The existing exclusion set remains:

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

Prohibited behavior includes:

- MGRS conversion;
- geographic accuracy assessment;
- local/projected/raster coordinate output;
- candidate score, order, rank, route, or waypoint changes.

## Source-Zone Metadata Boundary

These fields remain interpretation metadata:

```text
source_zone
source_sensitive
source_zone_reason
```

The report may count or display existing values. It must not:

- recalculate a score from `source_zone`;
- remove a candidate because `source_sensitive` is true;
- alter rank or record order from `source_zone_reason`;
- promote source metadata to an operational suitability result;
- represent metadata as measured real-world link quality.

## Artifact Handling Boundary

Task 029B is a pure formatter task. It includes:

- no file read;
- no file write;
- no path handling;
- no default report directory;
- no parent-directory creation;
- no overwrite policy;
- no repository sample report;
- no GitHub Actions artifact upload;
- no Git LFS;
- no package upload;
- no release asset.

Any report file output requires a separate reviewed CLI/file-output task. Runtime JSON, text, Markdown, CSV, PDF, image, and report artifacts remain outside the repository.

## CLI Surface Boundary

Task 029A and Task 029B add no CLI options.

The following proposed selectors are explicitly deferred:

```text
--report
--output-report PATH
```

Task 029B must not import `preview_cli`, modify `build_parser()`, alter source/output selector compatibility, print to stdout/stderr, or map formatter exceptions to process status codes.

A later Task 030A may define the CLI and explicit file-output boundary only after the pure formatter contract is implemented and tested.

## Task 029B Local Scope

Recommended branch:

```text
agent/task-029b-preview-report-formatter
```

Recommended additions:

```text
src/uav_rf_terrain/preview_report.py
tests/test_preview_report.py
docs/handoff/task-029b-preview-report-formatter.md
docs/paper/experiments/EXP-20260712-037-preview-report-formatter.md
```

`EXP-20260712-037` is reserved for Task 029B so the Task 029A boundary-plan record can retain `EXP-20260712-036` without an identifier collision.

Task 029B should:

- add `PreviewReportError`;
- add `format_preview_report(...)`;
- reuse existing preview/table validation;
- produce the fixed report sections;
- optionally include the existing appendix table;
- preserve input record order and values;
- add focused deterministic, validation, non-mutation, and no-file tests;
- update the handoff and experiment index;
- make no CLI, file-output, GIS, MGRS-conversion, scoring, route, or waypoint changes.

## Acceptance Criteria for Task 029B

Task 029B is acceptable when:

1. a valid preview mapping returns one deterministic report string;
2. the report includes the expected fixed headings;
3. the summary includes record count and MGRS external format;
4. the candidate overview summarizes existing counts and score ranges without changing data;
5. the source-zone section explains interpretation metadata;
6. user-facing candidate MGRS values may appear while internal/debug coordinate fields do not;
7. `include_table=True` includes the existing appendix-table output;
8. `include_table=False` omits the appendix-table section;
9. invalid preview input raises `PreviewReportError`;
10. the input mapping and nested records are not mutated;
11. no files or directories are created;
12. no CLI changes are made;
13. no preview schema or field changes are made;
14. no generated runtime artifacts are committed;
15. focused tests and the existing full test suite pass in the Local/CI environment.

## Non-Goals

Task 029A includes no:

- source-code changes;
- test changes;
- CLI-option changes;
- report formatter implementation;
- report stdout or report-file output;
- file writer or path policy;
- preview schema or field changes;
- appendix-table behavior changes;
- HTML rendering;
- PDF generation;
- image or figure generation;
- UI, table-widget, card, popup, or map rendering;
- real DEM/DSM/landcover or `METADATA_MAP` access;
- GIS dependency changes;
- MGRS conversion or geographic validation;
- field RF measurement validation;
- candidate rescoring or reranking;
- LOS/Fresnel recalculation;
- route or waypoint change;
- vehicle-control, flight-control, or external-device command output;
- generated runtime artifact commit.

## Follow-Up Tasks

1. Task 029B-Local: implement and test the pure preview report formatter only.
2. Task 030A-Cloud: define the report stdout and explicit file-output boundary after Task 029B is merged.
3. Task 030B-Local: implement report CLI/file output only after Task 030A approval.
4. A later UI task may consume reviewed preview mappings or report strings without changing the pure formatter contract.
5. Real-terrain integration remains a separate reviewed task requiring user-provided local data paths and Local verification.
6. Task 032CD does not expose its nested `DominantFresnelObstacle` in reports; a future report task must define an optional flat projection and display precision.
