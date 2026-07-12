# Task 026B-Local Preview JSON Input Table Output Prompt

## Role

You are the Local Execution Agent for the UAV RF Terrain Planner repository. Add one saved preview JSON input path to the existing table CLI surfaces, within the narrow scope below.

Preserve existing synthetic commands, output contracts, terrain/scoring boundaries, and public-repository restrictions.

## Repository

`leejinuk-minoan/uav-rf-terrain-planner`

## Base Branch

`main`

Create and use:

`agent/task-026b-preview-json-input-table-output`

Confirm Task 026A is merged before editing.

## Task

Task 026B-Local - Preview JSON Input Table Output

## Objective

Add the minimal input option:

```text
--input-json PATH
```

Supported saved-input commands:

```text
python -m uav_rf_terrain.preview_cli --input-json PATH --table
python -m uav_rf_terrain.preview_cli --input-json PATH --output-table PATH
```

Read the saved preview JSON as UTF-8, require a top-level object, pass it to the existing appendix-table formatter, and preserve all current synthetic behavior.

## Read First

Read before editing:

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `docs/architecture/current-candidate-preview-pipeline.md`
- `docs/architecture/preview-output-boundary-plan.md`
- `docs/architecture/preview-cli-output-contract.md`
- `docs/architecture/preview-appendix-table-plan.md`
- `docs/architecture/preview-table-output-surface-plan.md`
- `docs/architecture/preview-json-input-boundary-plan.md`
- `src/uav_rf_terrain/preview_cli.py`
- `src/uav_rf_terrain/preview_appendix_table.py`
- `src/uav_rf_terrain/synthetic_candidate_preview_smoke.py`
- `tests/test_preview_cli.py`
- `tests/test_preview_cli_contract.py`
- `tests/test_preview_appendix_table.py`
- `tests/test_preview_table_cli_output.py`
- `docs/handoff/task-025a-preview-table-output-surface-plan.md`
- `docs/handoff/task-025b-preview-table-cli-output.md`
- `docs/handoff/task-026a-preview-json-input-boundary-plan.md`
- `docs/paper/experiments/EXP-20260712-029-preview-table-output-surface-plan.md`
- `docs/paper/experiments/EXP-20260712-030-preview-table-cli-output.md`
- `docs/paper/experiments/EXP-20260712-031-preview-json-input-boundary-plan.md`
- `docs/paper/experiments/README.md`

Confirm the working tree is clean.

## Implementation Scope

Implement only:

1. Add `--input-json PATH`.
2. Define `--synthetic` and `--input-json PATH` as source selectors.
3. Require exactly one source selector.
4. Preserve every current `--synthetic` command.
5. Permit saved input only with `--table` or `--output-table PATH`.
6. Read the input as UTF-8 JSON.
7. Require the JSON top level to be an object/mapping.
8. Pass the decoded mapping to `format_preview_appendix_table(...)`.
9. Pass `--max-records` as formatter `max_rows`.
10. Reuse the existing text writer and `--force` for table-file output.
11. Do not call synthetic preview generation for `--input-json`.
12. Handle input read/decode/schema/formatter failures as concise status-1 errors.
13. Preserve status 2 for argument errors and status 3 for output-file errors.
14. Add focused tests and concise task records.

Do not duplicate the formatter or add another CLI module.

## Suggested Files

Expected production change:

```text
src/uav_rf_terrain/preview_cli.py
```

Preferred new test file:

```text
tests/test_preview_json_input_table_output.py
```

Only when necessary, minimally update:

```text
tests/test_preview_table_cli_output.py
tests/test_preview_cli_contract.py
tests/test_preview_cli.py
```

Add concise records:

```text
docs/handoff/task-026b-preview-json-input-table-output.md
docs/paper/experiments/EXP-20260712-032-preview-json-input-table-output.md
```

Update the experiment index once. Do not commit generated JSON or table files.

## CLI Options

Add:

```text
--input-json PATH
```

Keep all existing options and meanings:

```text
--synthetic
--max-records N
--json
--table
--output-json PATH
--output-text PATH
--output-table PATH
--force
```

The current parser-level `required=True` on `--synthetic` may be removed only to support explicit exactly-one-source validation.

## Source Selector Policy

Source selectors:

```text
--synthetic
--input-json PATH
```

Required behavior:

- exactly one source selector must be active;
- no source returns status 2;
- both sources return status 2;
- existing synthetic commands remain valid;
- input JSON commands do not invoke `build_synthetic_candidate_preview_smoke(...)`;
- source validation occurs before input reading or output generation.

Use concise stderr with no traceback.

## Output Selector Compatibility

Current output selectors remain mutually exclusive:

```text
--json
--table
--output-json PATH
--output-text PATH
--output-table PATH
```

For `--input-json`, support only:

```text
--table
--output-table PATH
```

Reject with status 2:

```text
--input-json PATH
--input-json PATH --json
--input-json PATH --output-json PATH
--input-json PATH --output-text PATH
```

Also retain all existing output-selector conflict checks.

`--max-records` and `--force` are not output selectors. `--max-records` limits table rows through `max_rows`; `--force` applies only to explicit output overwrite.

## Input File Policy

For `--input-json PATH`:

- use only the explicit selected path;
- do not discover paths or expand globs in application code;
- do not define a default path;
- require the path to exist and be a file;
- reject directories;
- read UTF-8 text;
- decode standard JSON;
- require a top-level object/mapping;
- do not mutate or rewrite the input;
- do not access real terrain or `METADATA_MAP`;
- use `tmp_path` for tests.

A small helper such as `_read_preview_json(path: Path) -> dict[str, object]` is acceptable. Do not duplicate formatter schema checks in that helper.

## JSON Decode and Schema Error Policy

Handle as status 1:

- missing input;
- directory input;
- unreadable input;
- invalid UTF-8;
- invalid JSON;
- non-object top level;
- missing preview or record fields;
- invalid MGRS contract;
- internal/debug coordinate fields;
- record-count mismatch;
- invalid score or `source_sensitive` type;
- any other `PreviewAppendixTableError`.

Required failure behavior:

- concise stderr;
- no traceback;
- no partial table stdout;
- no created or replaced output file;
- unchanged input file.

Catch only expected input/formatting exceptions. Do not mask unrelated programming errors broadly.

## Status Code Policy

Preserve:

```text
0 = success
1 = handled preview/input/formatter error
2 = parser / argument error
3 = handled output-file error
```

Mappings:

- valid table stdout/file: 0;
- input read/decode/top-level/schema/formatter error: 1;
- missing/conflicting source: 2;
- output-selector conflict or unsupported input/output combination: 2;
- output path/write problem: 3.

Input path problems must not be mapped to status 3. Existing synthetic command statuses must remain unchanged.

## MGRS Boundary

Input and table output must preserve:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
```

Use the existing formatter contract. Show no other candidate coordinate column. Do not implement coordinate conversion or geographic-accuracy assessment.

## Internal/Debug Coordinate Boundary

Reject and never display:

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

Add CLI-level tests for top-level and record-level rejection, status 1, no partial output, and no output-file creation or replacement.

## Source-Zone Metadata Boundary

Preserve existing:

```text
source_zone
source_sensitive
source_zone_reason
```

Treat these only as interpretation metadata. Do not use them to change score, order, rank, color, route, or waypoint values.

## Tests Required

At minimum cover:

1. Valid input JSON with `--table` returns 0 and a deterministic table.
2. Valid input JSON with `--output-table` returns 0 and writes UTF-8 text.
3. Table stdout and file have the same semantics.
4. `--max-records 3` limits rows and preserves the omission line.
5. `--force` reuses existing overwrite behavior.
6. Exactly one source is required.
7. Source conflict returns 2.
8. Input JSON without table output returns 2.
9. Input JSON with `--json`, `--output-json`, or `--output-text` returns 2.
10. Existing output-selector conflicts remain status 2.
11. Existing synthetic commands remain unchanged.
12. Input mode does not call synthetic generation.
13. Missing input returns 1.
14. Directory input returns 1.
15. Unreadable input returns 1 where the platform permits a reliable test.
16. Invalid UTF-8 returns 1.
17. Invalid JSON returns 1.
18. JSON array, scalar, string, boolean, and null top levels return 1.
19. Missing top-level field returns 1.
20. Missing record field returns 1.
21. Record-count mismatch returns 1.
22. Invalid score type returns 1.
23. Invalid `source_sensitive` type returns 1.
24. Invalid top-level or record-level MGRS contract returns 1.
25. Top-level or record internal coordinate key returns 1.
26. Input/formatter failures emit no partial table.
27. Input/formatter failures create no output file.
28. Existing output file remains unchanged after input failure.
29. Output missing-parent and directory-target errors remain 3.
30. Table retains record order and display-only row numbers.
31. MGRS and source-zone metadata remain present.
32. Internal/debug coordinate tokens remain absent.
33. Input mapping is not mutated.
34. Existing formatter, CLI, and contract tests remain passing.
35. No generated file is staged or committed.

Use `capsys`, `tmp_path`, `monkeypatch`, and direct `run_preview_cli(...)` calls where practical.

## Forbidden Changes

Do not:

- change preview JSON fields or formatter columns;
- change existing plain-text, JSON, or table semantics;
- add JSON copying or default input discovery;
- reconstruct plain-text preview from saved JSON;
- create parent directories automatically;
- add report generation or UI/map/card/popup/HTML rendering;
- access real terrain or `METADATA_MAP`;
- add GIS dependencies;
- change `pyproject.toml`, `.github/workflows/ci.yml`, or `docs/deployment/android-tmmr-offline-plan.md`;
- implement MGRS conversion or coordinate-accuracy assessment;
- change scoring, LOS/Fresnel, route, waypoint, sorting, ranking, or rescoring;
- add external execution-system integration or automated vehicle output;
- commit raster, archive, QGIS, CSV, PDF, image, generated JSON, generated TXT, or generated Markdown output;
- expose private paths, sensitive coordinates, credentials, tokens, or secrets;
- add unsupported outcome claims.

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

git diff --name-only | grep -E '\.(tif|tiff|img|vrt|zip|aux\.xml|ovr|qgz|qgs|png|jpg|jpeg|webp|svg|csv|pdf)$' && echo "FORBIDDEN DATA FILE" || true

git diff --name-only | grep '^METADATA_MAP/' && echo "METADATA_MAP FILE COMMITTED" || true
```

Run representative smoke with temporary paths only:

```text
python -m uav_rf_terrain.preview_cli --input-json <TEMP_JSON> --table
python -m uav_rf_terrain.preview_cli --input-json <TEMP_JSON> --table --max-records 3
python -m uav_rf_terrain.preview_cli --input-json <TEMP_JSON> --output-table <TEMP_TABLE>
```

Remove temporary outputs after smoke.

## Commit and PR

Suggested commit:

```text
feat: add preview json input table output
```

Suggested PR title:

```text
feat: add preview json input table output
```

PR body must state implemented source selection, supported saved-input table modes, error/status behavior, tests, unchanged synthetic modes, and excluded scope. Do not merge without user approval.

## Completion Report Format

```text
Task:
Branch:
PR:
Base commit:
Commit:
Changed files:
CLI option:
Source selector behavior:
Output compatibility:
Input file behavior:
Decode/schema error handling:
Status codes:
MGRS handling:
Internal/debug coordinate handling:
Source-zone handling:
Existing synthetic compatibility:
Tests and smoke:
Protected file check:
Generated-file check:
Private path check:
CI:
Limitations:
Ready for GPT Master review:
```
