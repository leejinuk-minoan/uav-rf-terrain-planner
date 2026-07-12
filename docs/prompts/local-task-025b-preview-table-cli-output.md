# Task 025B-Local Preview Table CLI Output Prompt

## Role

You are the Local Execution Agent for the UAV RF Terrain Planner repository. Connect the existing preview appendix-table formatter to the existing synthetic preview CLI only within the narrow scope below.

Do not change terrain, scoring, route, waypoint, report, UI, HTML, or existing preview contracts.

## Repository

`leejinuk-minoan/uav-rf-terrain-planner`

## Base Branch

`main`

Create and use:

`agent/task-025b-preview-table-cli-output`

## Task

Task 025B-Local - Preview Table CLI Output

## Objective

Expose the existing `format_preview_appendix_table(...)` formatter through two minimal synthetic CLI surfaces:

```text
--table
--output-table PATH
```

The implementation must preserve every currently valid CLI command and reuse the existing formatter, preview dictionary, explicit-path policy, overwrite policy, MGRS boundary, status-code meanings, and generated-artifact restrictions.

## Read First

Read these files before editing:

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `docs/architecture/current-candidate-preview-pipeline.md`
- `docs/architecture/preview-output-boundary-plan.md`
- `docs/architecture/preview-cli-output-contract.md`
- `docs/architecture/preview-appendix-table-plan.md`
- `docs/architecture/preview-table-output-surface-plan.md`
- `src/uav_rf_terrain/preview_cli.py`
- `src/uav_rf_terrain/candidate_display_preview.py`
- `src/uav_rf_terrain/preview_appendix_table.py`
- `src/uav_rf_terrain/synthetic_candidate_preview_smoke.py`
- `tests/test_preview_cli.py`
- `tests/test_preview_cli_contract.py`
- `tests/test_preview_appendix_table.py`
- `docs/handoff/task-023b-preview-contract-validation.md`
- `docs/handoff/task-024a-preview-appendix-table-plan.md`
- `docs/handoff/task-024b-preview-appendix-table-formatter.md`
- `docs/handoff/task-025a-preview-table-output-surface-plan.md`
- `docs/paper/experiments/EXP-20260712-026-preview-contract-validation.md`
- `docs/paper/experiments/EXP-20260712-027-preview-appendix-table-plan.md`
- `docs/paper/experiments/EXP-20260712-028-preview-appendix-table-formatter.md`
- `docs/paper/experiments/EXP-20260712-029-preview-table-output-surface-plan.md`

Confirm the working tree is clean before editing.

## Implementation Scope

Implement only the following:

1. Add `--table` to the existing parser as a boolean stdout mode.
2. Add `--output-table PATH` as one explicit file-output mode.
3. Extend existing output-mode conflict checks.
4. Reuse the existing synthetic preview build path.
5. Call `format_preview_appendix_table(result.preview_dict, max_rows=args.max_records)` only in table modes.
6. Print the table string to stdout in `--table` mode.
7. Reuse the existing text writer for `--output-table`.
8. Reuse `--force` for existing-file overwrite.
9. Handle `PreviewAppendixTableError` as a concise status-1 error.
10. Preserve status 2 for parser/argument errors.
11. Preserve status 3 for output-path and write errors.
12. Preserve existing default, JSON, JSON-file, and text-file behavior.
13. Add focused tests.
14. Add concise handoff and experiment records under repository conventions.

Do not add a separate CLI module or duplicate the formatter.

## Suggested Files

Expected production change:

```text
src/uav_rf_terrain/preview_cli.py
```

Expected tests:

```text
tests/test_preview_table_cli_output.py
```

Necessary focused additions may be made to:

```text
tests/test_preview_cli.py
tests/test_preview_cli_contract.py
```

Prefer a dedicated test file so existing contract tests remain readable.

Optional concise records:

```text
docs/handoff/task-025b-preview-table-cli-output.md
docs/paper/experiments/EXP-20260712-030-preview-table-cli-output.md
```

Do not create or commit generated table output.

## CLI Options

Add the following options:

```text
--table
--output-table PATH
```

Required semantics:

- `--table` prints the appendix-table formatter result to stdout.
- `--output-table PATH` writes the formatter result to the explicit selected path as UTF-8 text.
- `--max-records N` is passed to the formatter as `max_rows=N` for both table modes.
- `--force` permits overwrite for `--output-table` under the existing policy.
- No selector continues to mean the existing plain-text preview stdout.

Do not rename or remove any existing option.

## Mode Conflict Policy

Treat these as output selectors:

```text
--json
--table
--output-json PATH
--output-text PATH
--output-table PATH
```

At most one selector may be active.

Required invalid combinations include:

- `--json --table`
- `--json --output-json PATH`
- `--json --output-text PATH`
- `--json --output-table PATH`
- `--table --output-json PATH`
- `--table --output-text PATH`
- `--table --output-table PATH`
- `--output-json PATH --output-text PATH`
- `--output-json PATH --output-table PATH`
- `--output-text PATH --output-table PATH`

Each conflict returns status 2 and concise stderr without a traceback.

`--max-records` and `--force` are not output selectors. Do not introduce an unrelated behavior change for currently accepted uses of those options.

## Table Stdout Behavior

For:

```text
python -m uav_rf_terrain.preview_cli --synthetic --table
```

Required behavior:

- build the existing synthetic preview
- format `result.preview_dict`
- print the returned table string
- return status 0
- emit no stderr
- create no file
- preserve table column order and preview record order
- preserve display-only one-based row numbers
- preserve MGRS and source-zone metadata

For:

```text
python -m uav_rf_terrain.preview_cli --synthetic --table --max-records 3
```

Required behavior:

- display three data rows
- preserve row numbers 1 through 3
- preserve the formatter omission line
- do not alter the input preview dictionary

## Table File Output Behavior

For:

```text
python -m uav_rf_terrain.preview_cli --synthetic --output-table PATH
```

Required behavior:

- format the existing preview dictionary
- write only to the explicit path
- use UTF-8 text
- normalize to one trailing newline through the existing text writer
- print only `preview saved: <PATH>` or the existing equivalent confirmation to stdout
- do not print the table body to stdout
- return status 0

Path and overwrite rules:

- do not create parent directories
- missing parent returns status 3
- directory target returns status 3
- existing file without `--force` returns status 3 and remains unchanged
- `--force` permits overwrite
- no other file is created

Use `tmp_path` in tests. Do not stage the generated test output.

## Status Code Policy

Preserve:

```text
0 = success
1 = handled preview or formatter error
2 = parser or argument error
3 = handled file-output error
```

Catch `PreviewAppendixTableError` in the handled preview/formatting boundary. Error output must be concise and must not include a traceback.

Do not change existing status behavior for current commands.

## MGRS Boundary

Table stdout and table files must preserve:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
```

Do not display another candidate coordinate column.

Do not implement coordinate conversion and do not assess the geographic accuracy of supplied or synthetic placeholder MGRS values.

## Internal/Debug Coordinate Boundary

Table stdout and files must not expose:

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

The formatter already rejects these fields. Add CLI-level tests confirming they do not appear in table stdout or table files.

## Source-Zone Metadata Boundary

The table may display existing:

```text
source_zone
source_sensitive
source_zone_reason
```

Treat them only as interpretation metadata. Do not use them to change score, order, rank, color, route, or waypoint values.

## Tests Required

At minimum, cover:

1. `--table` returns status 0 and valid table stdout.
2. Table stdout contains all expected columns.
3. Table stdout preserves candidate record order.
4. Table stdout uses one-based display-only row numbers.
5. `--table --max-records 3` limits rows and preserves the omission line.
6. Table stdout creates no file.
7. `--output-table PATH` writes the same semantic table text as `--table`.
8. Table file uses UTF-8 and one trailing newline.
9. Successful table file output prints only the save confirmation.
10. `--output-table --max-records 3` limits rows and preserves the omission line.
11. Existing file is protected without `--force`.
12. `--force` overwrites the existing table file.
13. Missing parent returns status 3 and creates no directory.
14. Directory target returns status 3.
15. Every output-selector conflict returns status 2.
16. Formatter error returns status 1 without traceback.
17. MGRS values appear in table stdout and file output.
18. Internal/debug coordinate tokens do not appear.
19. Source-zone metadata appears without changing score or order.
20. Existing default plain-text mode remains unchanged.
21. Existing JSON stdout and JSON file remain complete when `--max-records` is supplied.
22. Existing text-file behavior remains unchanged.
23. Existing preview CLI contract tests remain passing.
24. Existing formatter tests remain passing.
25. No generated output file is staged or committed.

Use `capsys`, `tmp_path`, `monkeypatch`, and direct `run_preview_cli(...)` calls where practical.

## Forbidden Changes

Do not:

- change preview JSON fields
- change the existing plain-text preview formatter
- change appendix-table columns or formatter behavior
- add JSON-file input
- add automatic directory creation
- add implicit default output paths
- add report generation
- add UI, card, popup, map, or HTML rendering
- access real DEM, DSM, landcover, or `METADATA_MAP`
- add rasterio, GDAL, geopandas, or another GIS dependency
- change `pyproject.toml`
- change `.github/workflows/ci.yml`
- change `docs/deployment/android-tmmr-offline-plan.md`
- implement MGRS conversion
- assess MGRS geographic accuracy
- change candidate scoring, LOS/Fresnel, route, or waypoint logic
- sort or rank table rows
- add external execution-system integration or automated-control output
- commit raster, archive, QGIS, CSV, PDF, image, generated JSON, generated TXT, or generated Markdown table files
- expose private absolute paths, sensitive coordinates, credentials, tokens, or secrets
- add unsupported outcome claims

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

Run representative smoke commands using temporary paths only:

```text
python -m uav_rf_terrain.preview_cli --synthetic --table
python -m uav_rf_terrain.preview_cli --synthetic --table --max-records 3
```

Use a temporary directory for `--output-table` smoke and remove the output afterward.

## Commit and PR

Suggested commands:

```text
git add src/uav_rf_terrain/preview_cli.py tests/test_preview_table_cli_output.py tests/test_preview_cli.py tests/test_preview_cli_contract.py docs/handoff docs/paper/experiments README.md
git commit -m "feat: add preview table cli output"
git push origin agent/task-025b-preview-table-cli-output
```

Suggested PR title:

`feat: add preview table cli output`

The PR body must report:

- exact changed files
- new CLI options
- mode-conflict coverage
- table stdout and file behavior
- status-code behavior
- MGRS and internal-coordinate checks
- source-zone metadata behavior
- existing CLI compatibility
- local verification commands
- temporary-file smoke and cleanup
- GitHub Actions result
- explicit confirmation that no report, UI, terrain, scoring, route, or waypoint behavior changed

## Completion Report Format

```text
Task:
Branch:
PR:
Base commit:
Commit:
Changed files:
CLI options:
Mode conflict policy:
Table stdout behavior:
Table file behavior:
Status code behavior:
MGRS field handling:
Internal/debug coordinate handling:
Source-zone metadata handling:
Existing command compatibility:
Tests added:
Generated artifact cleanup:
Protected file check:
GIS/METADATA_MAP/generated-file check:
Private path check:
Restricted wording check:
Commands run:
Manual CLI smoke:
CI:
Local verification limits:
Ready for GPT Master review:
```
