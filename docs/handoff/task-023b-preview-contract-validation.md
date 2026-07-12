# Task 023B Preview Contract Validation

## Purpose

Task 023B adds regression tests for the existing synthetic preview CLI contract without changing production behavior.

## Covered contract

- Exact JSON top-level and record fields
- JSON stdout/file semantic equality
- Full JSON records when `--max-records` is supplied
- Plain-text headers, candidate row shape, aggregate source-sensitive count, and omission line
- Plain-text stdout/file formatter equality
- Deterministic status codes 0, 1, 2, and 3 with concise stderr
- Explicit output path, missing-parent, directory-target, overwrite, and mode-conflict policy
- `candidate_cell_mgrs` and `external_coordinate_format = MGRS`
- Internal/debug coordinate exclusion across stdout and files

## Unchanged behavior

No CLI option, JSON field, text formatter, status meaning, file-output behavior, preview schema, scoring logic, terrain access, report output, or UI behavior is changed. Production source files are unchanged.

## Data and repository boundary

Tests use `tmp_path`. No generated preview is committed. No real DEM/DSM/landcover, `METADATA_MAP`, GIS dependency, MGRS conversion, or sensitive coordinate is used.

## Verification

Local compile, full pytest, Ruff, mypy, diff checks, protected-path checks, and manual stdout/file smoke results are recorded in the Task 023B PR.

## Overall status

**passed locally and in GitHub Actions CI for PR #64 on the checked head commit**.

## Limitations

The validation fixes the current synthetic contract only. It does not assess placeholder MGRS geographic accuracy or field outcomes.
