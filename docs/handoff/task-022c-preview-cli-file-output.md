# Task 022C Preview CLI Explicit File Output

## Environment

- Windows local execution environment
- Repository base: PR #61 merge commit `65d370c`
- Standard-library `pathlib` and JSON serialization only

## Implemented scope

The synthetic preview CLI now accepts explicit `--output-json PATH` and `--output-text PATH` options. Existing plain-text and JSON stdout modes remain unchanged. `--force` permits overwriting an existing selected file; without it, existing content is preserved and the command returns status 3.

The CLI writes only to the user-specified path. It does not create parent directories, accepts only one output mode, rejects directory targets, and reports expected file errors without a traceback.

## Output boundary

- JSON files contain the complete existing preview dictionary as UTF-8 indented JSON.
- Text files contain the existing preview text; `--max-records` limits text rows.
- Output records preserve `candidate_cell_mgrs` and `external_coordinate_format = MGRS`.
- Internal/debug coordinate fields remain excluded.
- No MGRS conversion or geographic validation is performed.

## Terrain and repository boundary

No real DEM/DSM/landcover or `METADATA_MAP` input is accessed. No GIS dependency, rendering, scoring change, or automatic report generation is included. Manual smoke preview files are deleted after verification and are not committed.

## Verification

Local compile, full pytest, Ruff, mypy, diff checks, protected-path checks, and manual CLI smoke commands are recorded in the Task 022C PR. Tests use `tmp_path` for file output.

## Overall status

**passed locally and in GitHub Actions CI for PR #62 on the checked head commit**.

## Limitations

The CLI remains synthetic-only. Placeholder MGRS strings are not geographically validated, and explicit file output is a developer inspection scaffold rather than a report or UI.
