# Task 024B-Local Preview Appendix Table Formatter Prompt

## Role

You are the Local Execution Agent for the UAV RF Terrain Planner repository. Implement only the pure Python preview appendix-table formatter and focused tests described below. Do not change the existing preview CLI, JSON schema, file-output behavior, scoring, terrain, route, waypoint, report, or UI layers.

## Repository

`leejinuk-minoan/uav-rf-terrain-planner`

## Base Branch

`main`

Create and use:

`agent/task-024b-preview-appendix-table-formatter`

## Task

Task 024B-Local - Preview Appendix Table Formatter

## Objective

Add a pure Python formatter that converts the reviewed preview JSON dictionary into a deterministic Markdown/plain-text table string for paper-appendix preparation or developer inspection.

The formatter must consume the existing Tasks 023A/023B JSON contract without adding, removing, renaming, reordering as a requirement, or reinterpreting preview fields. It must not write files or add CLI behavior.

## Read First

Read these files before editing:

- `README.md`
- `AGENTS.md` if present
- `CLAUDE.md` if present
- `docs/architecture/current-candidate-preview-pipeline.md`
- `docs/architecture/preview-output-boundary-plan.md`
- `docs/architecture/preview-cli-output-contract.md`
- `docs/architecture/preview-appendix-table-plan.md`
- `src/uav_rf_terrain/candidate_display_preview.py`
- `src/uav_rf_terrain/preview_cli.py`
- `src/uav_rf_terrain/coordinate_io_policy.py`
- `tests/test_preview_cli.py`
- `tests/test_preview_cli_contract.py`
- `docs/handoff/task-023a-preview-cli-output-contract.md`
- `docs/handoff/task-023b-preview-contract-validation.md`
- `docs/handoff/task-024a-preview-appendix-table-plan.md`
- `docs/paper/experiments/EXP-20260712-025-preview-cli-output-contract.md`
- `docs/paper/experiments/EXP-20260712-026-preview-contract-validation.md`
- `docs/paper/experiments/EXP-20260712-027-preview-appendix-table-plan.md`

Confirm the working tree is clean before editing.

## Implementation Scope

Implement one narrowly scoped formatter layer:

1. Accept the existing preview JSON dictionary as an in-memory mapping.
2. Validate the required top-level fields.
3. Validate the required record fields.
4. Preserve the order of the input `records` list.
5. Derive one-based `row_no` values for table display only.
6. Return a deterministic Markdown/plain-text table string.
7. Display existing score values without recalculation.
8. Preserve `candidate_cell_mgrs` and the MGRS policy.
9. Preserve source-zone interpretation metadata.
10. Reject internal/debug coordinate fields.
11. Optionally limit visible rows with `max_rows`.
12. Add a deterministic omitted-row line when limited.
13. Create no file and add no CLI option.

Do not modify production modules outside the new formatter unless a minimal package export is clearly necessary. Any export-only change must remain non-breaking and must be documented.

## Suggested Files

Preferred implementation files:

```text
src/uav_rf_terrain/preview_appendix_table.py
tests/test_preview_appendix_table.py
```

Optional concise records when required by repository conventions:

```text
docs/handoff/task-024b-preview-appendix-table-formatter.md
docs/paper/experiments/EXP-20260712-028-preview-appendix-table-formatter.md
```

Do not create generated table, JSON, text, CSV, PDF, image, or report artifacts.

## Input Contract

The formatter input must follow the existing preview JSON contract.

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

Required validation includes:

- `preview` is a mapping
- `records` is a non-empty sequence of mappings
- `record_count` equals the number of records
- top-level `external_coordinate_format == "MGRS"`
- top-level `user_coordinate_field == "candidate_cell_mgrs"`
- every record has a non-empty `candidate_cell_mgrs`
- every record has `external_coordinate_format == "MGRS"`
- every record has `user_coordinate_field == "candidate_cell_mgrs"`
- `source_sensitive` is a boolean
- score values are numeric and are not recalculated
- top-level and record mappings contain no blocked internal/debug coordinate key

Do not add, remove, rename, or reinterpret preview JSON fields.

## Table Columns

Default table columns, in order:

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

`row_no` is derived by the formatter from preserved record order. It is not written back into the preview dictionary.

## Formatter Behavior

Recommended public function:

```python
format_preview_appendix_table(
    preview: Mapping[str, object],
    *,
    max_rows: int | None = None,
) -> str
```

Required behavior:

- return `str`
- use deterministic Markdown pipe-table or equivalent plain-text table formatting
- include one header row and one separator row
- preserve record order
- number displayed rows starting at 1
- display the recommended columns
- format score values consistently without changing their numeric meaning
- safely escape or normalize pipe characters and line breaks in text cells
- avoid relying on a Markdown rendering package
- do not mutate `preview`, `records`, or record mappings
- accept `max_rows=None` for all rows
- accept positive integer `max_rows`
- reject zero, negative, boolean, float, or string limits
- when rows are omitted, append a concise deterministic line such as:

```text
... 2 additional row(s) omitted.
```

- create no file
- add no CLI option

Use an explicit exception class such as `PreviewAppendixTableError` when that improves error consistency.

## MGRS Boundary

User-facing coordinates remain:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
```

The table displays `candidate_cell_mgrs` and no other candidate coordinate.

Do not implement MGRS conversion and do not assess the geographic accuracy of supplied or synthetic placeholder MGRS values.

## Internal/Debug Coordinate Boundary

Reject and do not display:

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

Reuse `INTERNAL_COORDINATE_FIELD_NAMES` where practical. Check both top-level and record mappings.

## Source-Zone Metadata Boundary

Display existing values:

```text
source_zone
source_sensitive
source_zone_reason
```

Treat them only as interpretation metadata. Do not use them to alter score, order, rank, color, route, or waypoint values.

## Tests Required

At minimum, add focused tests for:

1. A valid preview dictionary produces a string.
2. The table contains all recommended column names.
3. Input record order is preserved.
4. `row_no` begins at 1 and increments only for displayed rows.
5. `candidate_cell_mgrs` values are preserved.
6. `external_coordinate_format == "MGRS"` is required.
7. `user_coordinate_field == "candidate_cell_mgrs"` is required.
8. Existing `overall_score` and `shielding_stability_score` values are displayed without recalculation.
9. `source_zone`, `source_sensitive`, and `source_zone_reason` are displayed.
10. `candidate_reason` is displayed and text cells are safely normalized.
11. Internal/debug coordinate keys at the top level are rejected.
12. Internal/debug coordinate keys in records are rejected.
13. Missing required top-level field is rejected.
14. Missing required record field is rejected.
15. Empty records are rejected.
16. Record-count mismatch is rejected.
17. `max_rows=None` displays all rows.
18. Positive `max_rows` limits visible rows and adds the omission line.
19. Invalid limits are rejected.
20. The formatter does not mutate input values.
21. No file is created.
22. No GIS, raster, rendering, CLI, or file-writing dependency is imported by the new module.
23. Existing preview CLI and contract tests remain passing.

Use synthetic in-memory mappings or the existing synthetic preview dictionary. Do not create repository output artifacts.

## Forbidden Changes

Do not:

- add preview CLI options
- change `preview_cli.py` behavior
- change `candidate_display_preview.py` behavior
- change existing preview JSON fields
- change existing plain-text preview formatting
- change file-output behavior
- sort, rank, or recalculate records
- add report generation
- add UI/table/card/popup rendering
- add HTML rendering
- access real DEM, DSM, landcover, or `METADATA_MAP`
- add rasterio, GDAL, geopandas, or another GIS dependency
- change `pyproject.toml`
- change `.github/workflows/ci.yml`
- change `docs/deployment/android-tmmr-offline-plan.md`
- implement MGRS conversion
- assess MGRS geographic accuracy
- change candidate scoring, LOS/Fresnel, route, or waypoint logic
- add vehicle-control or autopilot output
- commit `.tif`, `.tiff`, `.img`, `.vrt`, `.zip`, `.aux.xml`, `.ovr`, `.qgz`, `.qgs`, `.png`, `.jpg`, `.jpeg`, `.webp`, `.svg`, `.csv`, `.pdf`, generated `.json`, generated `.txt`, or generated Markdown table files
- expose private absolute paths, sensitive coordinates, credentials, tokens, or secrets
- add unsupported operational claims

## Verification Commands

Run and record:

```text
python -m compileall src tests examples scripts
python -m pytest
python -m ruff check .
python -m mypy src
git diff --check
git status --short
git diff --name-only
```

Additional checks:

```text
git diff --name-only | grep -E '^(\.github/workflows/ci\.yml|pyproject\.toml|docs/deployment/android-tmmr-offline-plan\.md)$' && echo "FORBIDDEN PATH CHANGED" || true

git diff --name-only | grep -E '\.(tif|tiff|img|vrt|zip|aux\.xml|ovr|qgz|qgs|png|jpg|jpeg|webp|svg|csv|pdf|json|txt)$' && echo "CHECK GENERATED OR DATA FILE" || true

git diff --name-only | grep '^METADATA_MAP/' && echo "METADATA_MAP FILE COMMITTED" || true

grep -n "C:\\Users\|/Users/\|/home/\|file://" -R README.md docs src tests examples || true
```

Run a direct formatter smoke in memory. Do not leave output files.

## Commit and PR

Suggested commands:

```text
git add src/uav_rf_terrain/preview_appendix_table.py tests/test_preview_appendix_table.py docs/handoff docs/paper/experiments README.md
git commit -m "feat: add preview appendix table formatter"
git push origin agent/task-024b-preview-appendix-table-formatter
```

Suggested PR title:

`feat: add preview appendix table formatter`

The PR body must report:

- exact changed files
- formatter input and output contract
- table columns
- record-order and row-number behavior
- score-display behavior
- MGRS and internal-coordinate checks
- source-zone metadata behavior
- `max_rows` and omission behavior
- no-file/no-CLI confirmation
- local commands and direct formatter smoke
- GitHub Actions result
- confirmation that no terrain, scoring, route, waypoint, report, UI, or file-output behavior changed

## Completion Report Format

```text
Task:
Branch:
PR:
Base commit:
Commit:
Changed files:
Formatter module:
Input validation:
Table columns:
Ordering and row numbering:
Score handling:
MGRS field handling:
Internal/debug coordinate handling:
Source-zone metadata handling:
max_rows behavior:
File/CLI behavior:
Tests added:
Existing behavior changes:
Protected file check:
GIS/METADATA_MAP/generated-file check:
Private path check:
Restricted wording check:
Commands run:
Direct formatter smoke:
CI:
Local verification limits:
Ready for GPT Master review:
```
