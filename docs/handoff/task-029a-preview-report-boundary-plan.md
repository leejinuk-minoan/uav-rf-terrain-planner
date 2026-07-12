# Task 029A Preview Report Boundary Plan

## Purpose

Task 029A defines a safe documentation boundary for a future pure preview report formatter. The proposed formatter receives an existing reviewed preview mapping and returns a deterministic human-readable Markdown/plain-text report string.

This task is documentation only. It does not implement the report formatter, change the CLI, read or write report files, change preview fields, or alter runtime behavior.

## Documents Added

- `docs/architecture/preview-report-boundary-plan.md`
- `docs/prompts/local-task-029b-preview-report-formatter.md`
- `docs/handoff/task-029a-preview-report-boundary-plan.md`
- `docs/paper/experiments/EXP-20260712-036-preview-report-boundary-plan.md`

The experiment index receives one EXP-20260712-036 entry.

## Proposed Report Formatter Boundary

Recommended module and public function:

```text
src/uav_rf_terrain/preview_report.py
format_preview_report(preview: Mapping[str, object], *, include_table: bool = True) -> str
```

Recommended handled exception:

```text
PreviewReportError
```

The formatter is limited to a pure projection of the existing preview mapping. It performs no file I/O, CLI work, GIS/terrain access, coordinate conversion, scoring, LOS/Fresnel recalculation, route changes, waypoint changes, or external-device output.

The existing `format_preview_appendix_table(...)` function remains the preferred validation and optional table boundary.

## Proposed Report Sections

The proposed fixed section order is:

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

When `include_table=False`, the appendix-table heading and content are omitted together. No report row-limit option is introduced in Task 029B.

## Input Contract

The report formatter reuses the existing preview dictionary contract. It does not create a report-specific schema or add report-only fields.

Top-level compatibility fields include:

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

Record compatibility fields include:

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

Existing non-empty records, record-count equality, MGRS external format, user coordinate field, numeric/boolean type checks, and internal-coordinate rejection remain in force.

## Output Contract

The proposed output is one deterministic `str` intended for human review or a report draft.

It includes no path, file writing, stdout/stderr handling, HTML, image, PDF, map, UI, or generated repository artifact.

## Error Boundary

Invalid preview input should raise `PreviewReportError`. Existing `PreviewAppendixTableError` values may be caught and translated with exception chaining.

The pure formatter does not print handled errors or assign process status codes. Existing CLI status meanings remain unchanged, and report CLI mapping is deferred to a later task.

## Coordinate and Metadata Boundary

User-facing fields remain:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
source_zone
source_sensitive
source_zone_reason
```

The formatter displays existing MGRS text only. It does not convert coordinates or assess geographic correctness.

Internal/debug coordinate fields remain rejected, including local x/y, row/col, EPSG:5179 components, WGS84 components, and raster indices.

Source-zone fields remain interpretation metadata. They may be counted or displayed but must not change score, color, record order, LOS/Fresnel values, route values, or waypoint values.

## Artifact Handling Boundary

Task 029B includes no:

- file read or write;
- path handling;
- default output directory;
- parent-directory creation;
- overwrite policy;
- generated sample report;
- Actions artifact upload;
- Git LFS;
- package upload;
- release asset.

Report-file output is reserved for a separate boundary plan and Local implementation task.

## CLI Boundary

Task 029A and Task 029B do not add:

```text
--report
--output-report PATH
```

Task 029B must not modify `preview_cli.py`, source/output selector compatibility, process status mapping, or explicit file-output behavior.

## Task 029B Scope

Recommended additions:

```text
src/uav_rf_terrain/preview_report.py
tests/test_preview_report.py
docs/handoff/task-029b-preview-report-formatter.md
docs/paper/experiments/EXP-20260712-037-preview-report-formatter.md
```

Task 029B uses EXP-20260712-037. This avoids an identifier collision with the Task 029A boundary-plan record, which uses EXP-20260712-036.

Task 029B should implement the pure formatter, focused validation and non-mutation tests, optional exact appendix-table inclusion, handoff documentation, and an experiment-index entry. It must not add CLI or file-output behavior.

## Code/Test Change Check

- Source files changed by Task 029A: 0
- Test files changed by Task 029A: 0
- CLI options changed: 0
- Formatter behavior changed: 0
- Preview schema changes: 0
- Preview field changes: 0
- File-output behavior changes: 0
- Generated runtime artifacts committed: 0

## Test/CI Result

The Cloud Agent does not claim local compile, pytest, Ruff, mypy, CLI execution, JSON read/write, table generation, or report generation for this documentation-only task.

GitHub Actions is checked against the final PR head and reported in the completion report. The repository's current CI remains unchanged.

## Overall Status

The report work is separated into three reviewed boundaries:

1. Task 029A: pure formatter plan and Local prompt;
2. Task 029B: pure formatter implementation and focused tests;
3. Task 030A/030B: later report CLI and explicit file-output planning/implementation, only if approved.

This sequence preserves the existing preview JSON, table, CLI, coordinate, and artifact contracts.

## Limitations

Task 029A does not execute preview workflows, inspect generated output, implement report text, validate actual MGRS geography, access real terrain data, evaluate field RF measurements, alter scoring, or add an interactive surface.

The proposed candidate overview is limited to counts and ranges derived from existing preview values. It is not a new analytical model.

## Public Repository Sensitivity Check

Only repository Markdown documentation and an experiment-index update are included. No private path, credential, raster, GIS file, `METADATA_MAP` content, QGIS project, generated JSON/text/report input or output, CSV, PDF, image, archive, or external dataset is included.

The documentation avoids operational-outcome claims and external-device command behavior.

## Follow-Up Tasks

1. Merge Task 029A only after GPT Master review and successful CI on the final head.
2. Fill the Task 029A merge commit into the Task 029B Local prompt before execution.
3. Run Task 029B-Local as a narrow pure formatter implementation.
4. Review Task 030A only after Task 029B is merged and its formatter contract is stable.
5. Keep real-terrain integration and interactive presentation in separate reviewed tasks.
