# EXP-20260712-026 - Preview Contract Validation

## Experiment Purpose

Verify that the documented synthetic preview CLI output contract is protected by focused regression tests.

## Input Data

Existing in-memory synthetic candidate preview output only. No real terrain or GIS data is accessed.

## Method

Invoke `run_preview_cli()` with stdout, JSON, explicit file, limited-record, invalid-argument, and file-error cases. Parse structured output, compare stdout and file semantics, and inspect text formatting and coordinate exclusions.

## Expected Result

The existing JSON fields, text projection, MGRS boundary, status codes, and explicit file policy remain stable without production code changes.

## Actual Result

The dedicated contract suite passed locally together with the full repository test suite. Temporary files remained under test or smoke temporary directories and were cleaned up.

## Metrics

- JSON top-level fields fixed: 8
- JSON record fields fixed: 13
- Status codes covered: 4
- Production files changed: 0
- Generated preview files committed: 0

## CI / Local Test Result

Local compile, full pytest, Ruff, mypy, diff checks, and manual CLI smoke are recorded in the Task 023B PR. GitHub Actions CI completed successfully for PR #64 on the checked head commit.

## Interpretation

The current synthetic preview contract can be changed intentionally only with corresponding regression updates, while accidental field, formatting, or file-policy drift is detectable.

## Limitations

This experiment does not validate MGRS geographic correctness, real terrain integration, report rendering, UI behavior, or operational outcomes.

## Public Repository Sensitivity Check

Only tests and Markdown records are added. No private path, terrain raster, generated preview, CSV, PDF, image, QGIS project, or archive is included.
