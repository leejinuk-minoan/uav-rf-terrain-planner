# Task 023B-Local Preview Contract Validation Prompt

## Role

You are the Local Execution Agent for the UAV RF Terrain Planner repository. Work only within the contract-regression scope below. Do not add user-facing features or change the existing CLI contract.

## Repository

`leejinuk-minoan/uav-rf-terrain-planner`

## Base Branch

`main`

Create and use:

`agent/task-023b-preview-contract-validation`

## Task

Task 023B-Local - Preview Contract Validation

## Objective

Strengthen automated regression coverage for the existing synthetic preview CLI output contract without adding CLI options, changing output fields, changing file behavior, or implementing report/UI surfaces.

The current contract includes:

- plain-text stdout
- JSON stdout
- explicit JSON file output
- explicit plain-text file output
- status codes 0, 1, 2, and 3
- MGRS user-facing candidate fields
- internal/debug coordinate exclusion
- explicit path and overwrite rules

## Read First

Read these files before editing:

- `README.md`
- `AGENTS.md` if present
- `CLAUDE.md` if present
- `docs/architecture/current-candidate-preview-pipeline.md`
- `docs/architecture/preview-output-boundary-plan.md`
- `docs/architecture/preview-cli-output-contract.md`
- `src/uav_rf_terrain/preview_cli.py`
- `src/uav_rf_terrain/candidate_display_preview.py`
- `src/uav_rf_terrain/candidate_display_outputs.py`
- `src/uav_rf_terrain/synthetic_candidate_preview_smoke.py`
- `src/uav_rf_terrain/coordinate_io_policy.py`
- `tests/test_preview_cli.py`
- `docs/handoff/task-022b-preview-cli-scaffold.md`
- `docs/handoff/task-022c-preview-cli-file-output.md`
- `docs/handoff/task-023a-preview-cli-output-contract.md`

Confirm the working tree is clean before editing.

## Implementation Scope

Implement regression checks only:

1. Assert the current JSON top-level contract.
2. Assert the current JSON record-level contract.
3. Assert that JSON stdout and JSON file data are semantically equivalent.
4. Assert that `--max-records` affects plain text but not JSON records.
5. Assert the current plain-text headers, visible row shape, source-sensitive aggregate count, and omission message.
6. Assert status codes 0, 1, 2, and 3.
7. Assert explicit file path, missing-parent, directory-target, overwrite, and mode-conflict behavior.
8. Assert MGRS fields remain present.
9. Assert internal/debug coordinate names remain absent.
10. Keep all existing user-facing behavior unchanged.

Do not implement report, table, card, popup, or UI output.

## Suggested Files

Prefer a separate contract test file:

```text
tests/test_preview_cli_contract.py
```

It is acceptable to add focused assertions to `tests/test_preview_cli.py` when separation would create unnecessary duplication, but a dedicated contract test is preferred.

Test-only helper functions may be placed inside the test module. Avoid adding production helpers unless there is a demonstrated need and the change is approved before implementation.

## JSON Contract Validation

Validate the actual current top-level fields:

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

Validate the actual current record fields:

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

Required checks:

- JSON stdout parses with `json.loads(...)`.
- JSON file parses with `json.loads(...)`.
- JSON stdout and JSON file are semantically equal for the same synthetic invocation.
- Top-level values use JSON-compatible types.
- Record values use strings, numbers, and booleans.
- `external_coordinate_format == "MGRS"`.
- `user_coordinate_field == "candidate_cell_mgrs"`.
- Every record has a non-empty `candidate_cell_mgrs`.
- Every record contains `source_zone`, `source_sensitive`, and `source_zone_reason`.
- Dataclass or enum representations are not emitted.
- `--max-records` does not truncate JSON stdout or JSON file records.

Do not add, remove, rename, or reinterpret JSON fields.

## Plain-Text Contract Validation

Validate the actual current plain-text output:

- title: `Candidate display preview`
- external coordinate format line
- user coordinate field line
- total record count line
- aggregate source-sensitive record count line
- visible candidate rows containing candidate ID, MGRS, color, score, and `source_zone`
- omission line when `--max-records` truncates rows

The current plain-text rows do not include per-record `source_sensitive` or `source_zone_reason`. Do not change the formatter or write tests that require those fields in text. Structured consumers must use JSON.

Plain-text stdout and plain-text file content should be equivalent apart from the file helper normalizing one trailing newline and stdout printing behavior.

## Status Code Validation

Add or preserve deterministic regression checks:

| Status | Meaning |
|---:|---|
| 0 | Successful stdout or file output |
| 1 | Handled preview generation error |
| 2 | Parser or argument error |
| 3 | Handled file-output error |

Expected stderr must remain concise and must not include a traceback.

## File Output Policy Validation

Validate:

- only the explicitly selected path is written
- parent directories are not created
- missing parent directory returns status 3
- directory target returns status 3
- existing content is preserved without `--force`
- `--force` permits overwrite
- JSON file uses UTF-8 and parses successfully
- text file uses UTF-8 and contains the existing formatter output
- JSON and text file modes cannot be combined
- JSON stdout cannot be combined with either file mode
- generated files are kept under `tmp_path` or another temporary directory and cleaned up by the test environment
- no generated preview file is staged or committed

## MGRS Boundary

All user-facing candidate coordinates remain:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
```

Do not implement coordinate conversion or geographic-correctness assessment. Reuse the existing synthetic placeholder values.

## Internal/Debug Coordinate Boundary

User-facing stdout and file outputs must not expose:

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

Use `INTERNAL_COORDINATE_FIELD_NAMES` where practical rather than duplicating policy values in production code.

## Tests Required

At minimum, cover:

1. Exact required JSON top-level keys.
2. Exact required JSON record keys.
3. JSON stdout/file semantic equality.
4. JSON primitive type checks.
5. JSON completeness when `--max-records` is provided.
6. Plain-text stdout headers and visible row shape.
7. Plain-text file equivalence and trailing newline behavior.
8. Omission message and visible row count.
9. Status codes 0, 1, 2, and 3.
10. Missing parent, directory target, overwrite protection, and forced overwrite.
11. Conflicting mode parser errors.
12. MGRS fields and internal-coordinate exclusion.
13. No unexpected file creation in stdout modes.
14. Existing `tests/test_preview_cli.py` remains passing.

Use `capsys`, `tmp_path`, `monkeypatch`, and direct `run_preview_cli(...)` calls where practical. Avoid OS-specific path assumptions.

## Forbidden Changes

Do not:

- add or remove CLI options
- add, remove, or rename JSON fields
- change plain-text row formatting
- change status-code meanings
- change file-output behavior
- change preview schema or candidate display schema
- access real DEM, DSM, landcover, or `METADATA_MAP`
- add GIS dependencies
- change `pyproject.toml`
- change `.github/workflows/ci.yml`
- change `docs/deployment/android-tmmr-offline-plan.md`
- generate reports
- implement UI or rendering surfaces
- implement coordinate conversion
- change candidate scoring, LOS/Fresnel, route, or waypoint logic
- add vehicle execution behavior
- commit raster, archive, CSV, PDF, image, diagram, QGIS project, or generated preview files
- expose private absolute paths, credentials, secrets, or sensitive coordinates
- add operational assurance claims

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

Run representative manual commands without leaving generated artifacts:

```text
python -m uav_rf_terrain.preview_cli --synthetic
python -m uav_rf_terrain.preview_cli --synthetic --max-records 3
python -m uav_rf_terrain.preview_cli --synthetic --json
```

Use a temporary directory for explicit file-output smoke and remove generated files afterward.

## Commit and PR

Suggested commit:

```text
git add tests/test_preview_cli_contract.py tests/test_preview_cli.py README.md docs/handoff docs/paper/experiments
git commit -m "test: validate preview cli output contract"
git push origin agent/task-023b-preview-contract-validation
```

Suggested PR title:

`test: validate preview cli output contract`

The PR body must record:

- exact changed files
- JSON and plain-text contracts tested
- status-code and file-policy coverage
- commands and manual smoke results
- MGRS and internal-coordinate checks
- generated-file cleanup
- GitHub Actions result
- explicit confirmation that no CLI option, schema, report, UI, terrain, or scoring behavior was added

## Completion Report Format

```text
Task:
Branch:
PR:
Base commit:
Commit:
Changed files:
Contract test file:
JSON contract checks:
Plain-text contract checks:
Status code checks:
File output policy checks:
MGRS field handling:
Internal/debug coordinate handling:
Existing behavior changes:
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