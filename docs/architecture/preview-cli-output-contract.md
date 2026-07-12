# Preview CLI Output Contract

## Purpose

This document records the current user-facing contract of the synthetic candidate preview CLI after Tasks 022B and 022C. It fixes the supported output modes, JSON and plain-text shapes, process status codes, explicit file policy, MGRS boundary, and internal-coordinate exclusion before any later report or UI work begins.

## Current CLI Surface

The current module supports:

```text
python -m uav_rf_terrain.preview_cli --synthetic
python -m uav_rf_terrain.preview_cli --synthetic --max-records 3
python -m uav_rf_terrain.preview_cli --synthetic --json
python -m uav_rf_terrain.preview_cli --synthetic --output-json PATH
python -m uav_rf_terrain.preview_cli --synthetic --output-text PATH
python -m uav_rf_terrain.preview_cli --synthetic --output-json PATH --force
python -m uav_rf_terrain.preview_cli --synthetic --output-text PATH --force
```

`--synthetic` is required. `--max-records` accepts a positive integer. `--json`, `--output-json`, and `--output-text` select mutually exclusive output modes. `--force` is relevant only when an explicit file target already exists.

## Output Modes

| Mode | CLI option | Output destination | Output object/source | Affected by `--max-records` | Contains full preview records | File creation behavior | Intended consumer | Follow-up task |
|---|---|---|---|---|---|---|---|---|
| Plain-text stdout | default after `--synthetic` | stdout | `SyntheticCandidatePreviewSmokeResult.preview_text` | Yes | No; human-readable projection only | None | Human CLI inspection | Contract regression in Task 023B |
| JSON stdout | `--json` | stdout | `SyntheticCandidatePreviewSmokeResult.preview_dict` | No | Yes | None | Machine parser and structured inspection | Contract regression in Task 023B |
| JSON file | `--output-json PATH` | User-selected file | Complete `preview_dict` serialized as UTF-8 indented JSON | No | Yes | Creates or overwrites only the selected file according to policy | Machine parser and later formatter | Contract regression in Task 023B; later report task may consume it |
| Plain-text file | `--output-text PATH` | User-selected file | Existing `preview_text` | Yes | No; human-readable projection only | Creates or overwrites only the selected file according to policy | Human review and saved smoke record | Contract regression in Task 023B |

`--max-records` changes only the plain-text formatter. JSON stdout and JSON file output continue to contain the complete preview dictionary.

## JSON Stdout Contract

`--json` prints standard-library JSON serialization of the existing preview dictionary to stdout. The current top-level fields are:

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

The principal record fields are:

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

The required minimum fields for downstream contract checks are:

- top level: `title`, `external_coordinate_format`, `user_coordinate_field`, `record_count`, `records`, `summary`
- record level: `candidate_id`, `candidate_cell_mgrs`, `source_zone`, `source_sensitive`, `source_zone_reason`

Record values are user-facing JSON primitive values: strings, numbers, and booleans. The top-level object additionally contains a list of records and a summary object. Dataclass, enum, or other Python runtime objects are not emitted directly.

JSON stdout uses `ensure_ascii=False`. It is compact output intended for machine parsing rather than stable whitespace comparison.

## JSON File Contract

JSON file output contains the same complete preview dictionary and record fields as JSON stdout. The semantic data contract is the same; presentation differs:

- UTF-8 text
- `ensure_ascii=False`
- indentation level 2
- one trailing newline

The JSON file is not affected by `--max-records` because that option changes only the plain-text projection.

On success, file content is written only to the explicit path and stdout contains a short `preview saved:` confirmation rather than the JSON payload.

## Plain-Text Stdout Contract

Default mode prints the existing human-readable preview string. Its current structure contains:

```text
Candidate display preview
External coordinate format: MGRS
User coordinate field: candidate_cell_mgrs
Records: <count>
Source-sensitive records: <count>
- <candidate_id> | <candidate_cell_mgrs> | <color_class> | score=<overall_score> | source_zone=<source_zone>
```

When visible rows are limited, the final line follows this form:

```text
... <count> additional record(s) omitted.
```

The current plain-text contract exposes:

- the preview title
- `external_coordinate_format`
- `user_coordinate_field`
- each visible `candidate_cell_mgrs`
- per-row `source_zone`
- an aggregate source-sensitive record count
- an omitted-record message when truncation occurs

The current implementation does not print per-record `source_sensitive` or `source_zone_reason` in plain-text rows. Those fields remain available in JSON stdout and JSON file output. This document records that actual behavior rather than declaring fields that the formatter does not emit.

Plain text is for human inspection and is not a machine-parsing contract. Consumers requiring stable structured fields must use JSON.

## Plain-Text File Contract

Plain-text file output contains the same `preview_text` used by default stdout mode, normalized to one trailing newline. `--max-records` limits visible rows and preserves the omitted-record message.

On success, the selected file contains the preview text and stdout contains a short `preview saved:` confirmation. The file is intended for human review, not structured parsing.

## Status Code Contract

| Status | Meaning | Current trigger |
|---:|---|---|
| 0 | Success | Plain-text stdout, JSON stdout, or explicit file output completes |
| 1 | Expected preview generation error | Existing preview or synthetic smoke helper raises a handled preview error |
| 2 | Parser or argument error | Missing `--synthetic`, invalid `--max-records`, or conflicting output modes |
| 3 | File-output error | Missing parent directory, directory target, protected existing file, or another handled write error |

Expected errors are reported concisely to stderr without a traceback.

## File Output Policy

The current explicit file policy is:

- write only to a user-selected explicit path
- do not create output directories automatically
- fail when the parent directory does not exist
- fail when the selected target is a directory
- preserve an existing file and return status 3 when `--force` is absent
- allow overwrite when `--force` is present
- do not use JSON file and plain-text file modes together
- do not combine JSON stdout mode with either file-output mode
- use UTF-8 text output
- do not commit generated preview files to the repository
- use `tmp_path` or another temporary directory for tests and local smoke work

`--output-json` and `--output-text` select one explicit target. Successful file output prints only the save confirmation to stdout.

## MGRS External Coordinate Boundary

All user-facing candidate coordinates remain:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
```

Stdout, explicit files, later reports, and future UI consumers must preserve this boundary. The current CLI consumes existing synthetic placeholder MGRS values. It does not convert coordinates or assess the geographic correctness of supplied MGRS text.

## Internal/Debug Coordinate Exclusion

The following internal/debug coordinate fields are excluded from JSON records and plain-text output:

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

These values may remain in internal map-feature or raster-processing objects, but they are not part of the user-facing CLI contract.

## Source-Zone Metadata Contract

The structured preview record preserves:

```text
source_zone
source_sensitive
source_zone_reason
```

These fields are interpretation metadata. They do not alter candidate scoring, LOS/Fresnel values, route scoring, or waypoint scoring.

JSON modes expose all three fields per record. The current plain-text projection exposes `source_zone` per row and the aggregate source-sensitive count; it does not expose per-record `source_sensitive` or `source_zone_reason`.

## Synthetic-Only Boundary

The current CLI invokes only the existing synthetic preview path.

It does not:

- access real DEM, DSM, or landcover data
- access `METADATA_MAP`
- connect to real candidate generation
- connect to real-terrain route generation
- convert MGRS coordinates
- render a map, table, card, popup, or report

Real-terrain integration requires a separate reviewed task.

## Non-Goals

Task 023A does not:

- change source code or tests
- add CLI options
- add or remove preview fields
- change output behavior
- execute the CLI
- generate output files
- implement a report or UI
- add GIS dependencies
- access terrain data
- convert coordinates
- change candidate scoring, LOS/Fresnel, route, or waypoint logic
- add vehicle execution behavior

## Future Consumer Guidance

| Consumer | Recommended input | Notes |
|---|---|---|
| Human CLI inspection | Plain-text stdout | Quick smoke and developer inspection only |
| Machine parser | JSON stdout or JSON file | Use the structured field contract; do not parse plain text |
| Paper appendix table | JSON file | Use a separate reviewed formatter task |
| UI table/card | JSON-ready dictionary or record list | Use a separate UI task and preserve MGRS fields |
| Report generator | JSON file | Use a separate report task and keep source-zone metadata separate from scoring |

## Task 023B Local Implementation Scope

Task 023B should add contract regression coverage without adding features:

1. Add focused contract assertions, preferably in `tests/test_preview_cli_contract.py`.
2. Verify required top-level and record-level JSON fields.
3. Verify JSON primitive types and internal-coordinate exclusion.
4. Verify the current plain-text headers, row content, aggregate source-sensitive count, and omitted-record behavior.
5. Verify status codes 0, 1, 2, and 3.
6. Verify explicit path, missing-parent, directory-target, overwrite, and mode-conflict rules.
7. Keep existing CLI options, preview schema, and file behavior unchanged.
8. Run compileall, pytest, ruff, mypy, diff checks, and representative local CLI smoke commands.

## Acceptance Criteria for Task 023B

Task 023B is acceptable when:

- contract tests assert the actual current JSON top-level and record fields
- JSON stdout and JSON file data are semantically equivalent
- JSON modes retain all records even when `--max-records` is supplied
- plain-text modes obey the positive record limit and omission message
- tests do not claim per-record plain-text fields that are not currently emitted
- status codes 0, 1, 2, and 3 have regression coverage
- explicit file-output policy has regression coverage
- MGRS fields remain present in user-facing outputs
- internal/debug coordinate names remain absent
- no CLI option, preview field, output behavior, scoring, or terrain integration changes are introduced
- local verification commands and GitHub Actions complete successfully

## Follow-Up Tasks

1. Task 023B-Local: add focused contract regression tests only.
2. A later report task may transform reviewed JSON files into appendix tables.
3. A later UI task may consume the JSON-ready dictionary or record list.
4. Real-terrain CLI integration, if required, must be a separate task with its own data and coordinate review.