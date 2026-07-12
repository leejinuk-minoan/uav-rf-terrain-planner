# Task 023A Preview CLI Output Contract Documentation

## Purpose

Task 023A documents the current synthetic preview CLI contract across plain-text stdout, JSON stdout, explicit JSON/text files, process status codes, MGRS fields, source-zone metadata, and file policy. It is a documentation-only task.

## Documents Added

- `docs/architecture/preview-cli-output-contract.md`
- `docs/prompts/local-task-023b-preview-contract-validation.md`
- `docs/handoff/task-023a-preview-cli-output-contract.md`
- `docs/paper/experiments/EXP-20260712-025-preview-cli-output-contract.md`

README and the experiment index receive short summary entries only.

## Current CLI Surface

The documented commands are:

```text
python -m uav_rf_terrain.preview_cli --synthetic
python -m uav_rf_terrain.preview_cli --synthetic --max-records 3
python -m uav_rf_terrain.preview_cli --synthetic --json
python -m uav_rf_terrain.preview_cli --synthetic --output-json PATH
python -m uav_rf_terrain.preview_cli --synthetic --output-text PATH
python -m uav_rf_terrain.preview_cli --synthetic --output-json PATH --force
python -m uav_rf_terrain.preview_cli --synthetic --output-text PATH --force
```

The CLI remains synthetic-only and requires `--synthetic`.

## Output Contract Summary

The current output modes are:

1. Plain-text stdout for human inspection.
2. JSON stdout for structured inspection.
3. Explicit JSON file output for structured persistence.
4. Explicit plain-text file output for human-readable persistence.

`--max-records` affects plain-text rows only. JSON stdout and JSON files preserve the complete preview dictionary.

## JSON Contract

The current top-level JSON fields are:

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

The current record fields are:

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

JSON stdout and JSON file output use the same semantic dictionary. The file representation is UTF-8 indented JSON with a trailing newline. User-facing values are JSON-compatible primitives, lists, and dictionaries rather than Python runtime objects.

## Plain-Text Contract

Plain text contains the preview title, MGRS format line, `candidate_cell_mgrs` field line, total and source-sensitive counts, visible candidate rows, score, and `source_zone`. A positive record limit adds the existing omitted-record line.

The current row formatter does not print per-record `source_sensitive` or `source_zone_reason`. Those fields remain available through JSON. Plain text is for human inspection and is not a machine-parsing contract.

## Status Code Contract

| Status | Meaning |
|---:|---|
| 0 | Successful stdout or file output |
| 1 | Handled preview generation error |
| 2 | Parser or argument error |
| 3 | Handled file-output error |

Expected errors use concise stderr without a traceback.

## File Output Policy

- Write only to the explicit user-selected path.
- Do not create parent directories automatically.
- Fail when the parent does not exist.
- Fail when the target is a directory.
- Preserve existing files unless `--force` is supplied.
- Permit overwrite with `--force`.
- Reject simultaneous JSON/text file modes.
- Reject mixing JSON stdout with file output.
- Use UTF-8.
- Keep generated files outside repository commits.
- Use temporary directories for tests and smoke commands.

## MGRS External Coordinate Handling

The user-facing candidate coordinate remains `candidate_cell_mgrs`, and `external_coordinate_format` remains `MGRS`.

Task 023A documents existing behavior only. It does not convert coordinates or assess the geographic correctness of synthetic placeholder MGRS values.

## Internal/Debug Coordinate Handling

Local metric coordinates, raster indices, EPSG:5179 components, and WGS84 components remain internal/debug values. The documented blocked fields are:

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

These fields are not part of stdout or explicit file output.

## Source-Zone Metadata Handling

JSON records preserve:

```text
source_zone
source_sensitive
source_zone_reason
```

They are output interpretation metadata and do not change candidate scoring, LOS/Fresnel values, route scoring, or waypoint scoring.

Plain-text rows expose `source_zone`; the header exposes an aggregate source-sensitive count. Per-record `source_sensitive` and `source_zone_reason` remain JSON-only in the current implementation.

## Synthetic-Only Boundary

The current CLI invokes only the existing in-memory synthetic preview smoke. It does not access real terrain data, `METADATA_MAP`, real candidate generation, or real-terrain route generation.

## Recommended Task 023B Scope

Task 023B-Local should add contract regression tests only:

- JSON top-level and record fields
- JSON stdout/file semantic equality
- JSON completeness under `--max-records`
- plain-text headers, rows, and omission message
- status codes 0 through 3
- explicit path, overwrite, missing-parent, directory-target, and mode-conflict behavior
- MGRS fields and internal-coordinate exclusion

It must not add options, change fields, alter output behavior, generate reports, implement UI, access terrain data, or change scoring.

## Test/CI Result

No source or test code is changed by Task 023A. Cloud Agent does not run local commands. GitHub Actions is checked after PR creation and recorded in the experiment record and completion report.

## Overall Status

The current preview CLI now has one architecture reference that downstream tests, report formatters, and UI consumers can use without redefining its schema or file behavior.

## Limitations

This task does not:

- change source or test code
- execute the CLI
- generate files
- add options or fields
- change file behavior
- implement reports or UI
- access real terrain data
- add GIS dependencies
- convert coordinates
- change scoring, LOS/Fresnel, route, or waypoint logic

## Public Repository Sensitivity Check

Only Markdown documentation and short README/index updates are included. No private absolute path, sensitive coordinate, credential, secret, local terrain data, GIS file, generated preview, CSV, PDF, image, diagram, QGIS project, or archive is included.

## Follow-Up Tasks

1. Task 023B-Local: add focused preview CLI contract regression tests.
2. A later report task may consume reviewed JSON output.
3. A later UI task may consume the JSON-ready dictionary or record list.
4. Real-terrain CLI integration must remain a separate reviewed task.