# Task 022B-Local Preview CLI Scaffold Prompt

## Role

You are the Local Execution Agent for the UAV RF Terrain Planner repository. Work only within the scope below. Prefer a small, reviewable implementation and record every local command and result.

## Repository

`leejinuk-minoan/uav-rf-terrain-planner`

## Base Branch

`main`

Create and use:

`agent/task-022b-preview-cli-scaffold`

## Task

Task 022B-Local - Preview CLI Scaffold

## Objective

Implement a minimal Python CLI or module entrypoint that invokes the existing synthetic candidate preview smoke and writes either the existing plain-text preview or the existing JSON-ready preview to stdout.

The default behavior should print the plain-text preview. An optional JSON mode may print the preview dictionary as JSON. Do not add persistent file output.

## Read First

Read these files before editing:

- `README.md`
- `AGENTS.md` if present
- `CLAUDE.md` if present
- `docs/architecture/current-candidate-preview-pipeline.md`
- `docs/architecture/preview-output-boundary-plan.md`
- `src/uav_rf_terrain/candidate_display_preview.py`
- `src/uav_rf_terrain/synthetic_candidate_preview_smoke.py`
- `src/uav_rf_terrain/coordinate_io_policy.py`
- `tests/test_candidate_display_preview.py`
- `tests/test_synthetic_candidate_preview_smoke.py`
- `docs/handoff/task-022a-preview-output-boundary-plan.md`

Confirm the working tree is clean before making changes.

## Implementation Scope

Implement only a minimal stdout scaffold:

1. Invoke `build_synthetic_candidate_preview_smoke(...)`.
2. Print `preview_text` to stdout by default.
3. Support a positive optional record limit, preferably `--max-records`.
4. Optionally support `--json` to print `preview_dict` through `json.dumps(...)`.
5. Return a non-zero exit status for invalid arguments or expected preview errors.
6. Keep implementation independent of GIS libraries and local terrain files.
7. Preserve the existing preview and scoring contracts.
8. Add focused tests for the CLI/helper behavior.

Do not write files, create output directories, or add report/UI behavior.

## Suggested Files

The Local Agent may adjust names after reviewing the package structure, but the recommended minimal files are:

```text
src/uav_rf_terrain/preview_cli.py
tests/test_preview_cli.py
```

A minimal package export adjustment is allowed only when required for consistent project imports. Avoid unrelated refactoring.

## CLI Behavior

Recommended schema:

```text
python -m uav_rf_terrain.preview_cli --synthetic
python -m uav_rf_terrain.preview_cli --synthetic --max-records 3
python -m uav_rf_terrain.preview_cli --synthetic --json
```

Required behavior:

- `--synthetic` selects the existing synthetic smoke path.
- Default output is the existing plain-text preview.
- `--max-records N` accepts a positive integer and limits visible plain-text rows through the existing preview path.
- Invalid limits produce a concise stderr message and a non-zero exit status.
- The command must not access real terrain data or `METADATA_MAP`.
- The command must not create files.

The exact module filename or argument parser may be refined locally if the final contract remains small and documented.

## JSON Output Behavior

If JSON mode is implemented:

- `--json` prints the existing `preview_dict` to stdout.
- Use standard-library JSON serialization.
- Output must be valid JSON.
- Preserve the current dictionary keys and record values.
- Use UTF-8-safe serialization behavior.
- Do not write a JSON file.
- Do not inject internal/debug coordinate fields.
- Do not reinterpret source-zone metadata or scores.

If JSON mode materially expands the task, document the reason and keep Task 022B to plain-text stdout only rather than adding partial file-output behavior.

## MGRS Boundary

User-facing candidate coordinates must remain:

- field: `candidate_cell_mgrs`
- external coordinate format: `MGRS`

The CLI must reuse the existing synthetic placeholder MGRS values and existing preview dictionary/text. Do not implement coordinate conversion or geographic-correctness assessment.

## Internal/Debug Coordinate Boundary

The CLI stdout must not expose:

- `x_m`
- `y_m`
- `row`
- `col`
- `epsg5179_x_m`
- `epsg5179_y_m`
- `wgs84_lat`
- `wgs84_lon`
- `local_x_m`
- `local_y_m`
- `raster_row`
- `raster_col`

Do not add flags that reveal these values.

## Tests Required

Add focused tests covering, as applicable:

1. Default plain-text stdout output.
2. Presence of the preview title, `MGRS`, and `candidate_cell_mgrs`.
3. Positive `--max-records` handling and omitted-record text.
4. Invalid zero, negative, non-integer, or malformed limits.
5. JSON stdout parses successfully with `json.loads(...)`.
6. JSON output contains `external_coordinate_format == "MGRS"`.
7. JSON records contain `candidate_cell_mgrs`.
8. Plain-text and JSON stdout exclude internal/debug coordinate names.
9. No output file is created.
10. Existing candidate preview and synthetic smoke tests continue to pass.
11. Main/helper return code behavior is deterministic.

Use `capsys`, `capfd`, or direct helper testing as appropriate. Avoid subprocess tests unless they materially improve confidence and remain portable.

## Forbidden Changes

Do not:

- access or commit real DEM, DSM, or landcover data
- access or commit `METADATA_MAP` content
- add rasterio, GDAL, geopandas, or other GIS dependencies
- change `pyproject.toml` unless explicitly approved after a demonstrated necessity
- change `.github/workflows/ci.yml`
- change `docs/deployment/android-tmmr-offline-plan.md`
- implement file writing or output-directory handling
- implement report generation
- implement map, table, popup, HTML, Markdown, Streamlit, or Folium rendering
- implement MGRS conversion or coordinate-correctness assessment
- change candidate scoring, LOS/Fresnel, route scoring, or waypoint scoring
- add vehicle-control integration
- add claims about measured or assured operational performance
- commit CSV, PDF, image, diagram, QGIS project, raster, archive, or generated output files
- expose private absolute paths, credentials, secrets, or sensitive coordinates

## Verification Commands

Run and record the results of:

```text
python -m compileall src tests examples scripts
python -m pytest
python -m ruff check .
python -m mypy src
git diff --check
git status --short
git diff --name-only
```

Also check:

```text
git diff --name-only | grep -E '^(\.github/workflows/ci.yml|pyproject.toml|docs/deployment/android-tmmr-offline-plan.md)$' && echo "FORBIDDEN PATH CHANGED" || true

git diff --name-only | grep -E '\.(tif|tiff|img|vrt|zip|aux\.xml|ovr|qgz|qgs|png|jpg|jpeg|webp|svg|csv|pdf)$' && echo "FORBIDDEN DATA OR GENERATED FILE COMMITTED" || true

git diff --name-only | grep '^METADATA_MAP/' && echo "METADATA_MAP FILE COMMITTED" || true

grep -n "C:\\Users\|/Users/\|/home/\|file://" -R README.md docs src tests examples || true
```

Run a manual command smoke after tests, for example:

```text
python -m uav_rf_terrain.preview_cli --synthetic
python -m uav_rf_terrain.preview_cli --synthetic --max-records 3
python -m uav_rf_terrain.preview_cli --synthetic --json
```

If the final CLI contract differs, record the exact commands actually used.

## Commit and PR

Suggested commit:

```text
git add src/uav_rf_terrain/preview_cli.py tests/test_preview_cli.py README.md docs/handoff docs/paper/experiments
git commit -m "feat: add synthetic preview cli scaffold"
git push origin agent/task-022b-preview-cli-scaffold
```

Suggested PR title:

`feat: add synthetic preview cli scaffold`

The PR body must state:

- purpose and exact CLI contract
- changed files
- plain-text and JSON stdout behavior
- MGRS and internal-coordinate boundaries
- local commands and results
- GitHub Actions result
- explicit statement that file output, real terrain access, rendering, coordinate conversion, and scoring changes are not included

## Completion Report Format

```text
Task:
Branch:
PR:
Base commit:
Commit:
Changed files:
CLI entry/helper:
Plain-text stdout behavior:
JSON stdout behavior:
MGRS field handling:
Internal/debug coordinate handling:
Tests added/updated:
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