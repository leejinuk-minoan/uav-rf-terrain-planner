# EXP-20260712-030 - Preview Table CLI Output

## Experiment Purpose

Verify minimal stdout and explicit file exposure of the existing preview appendix-table formatter.

## Input Data

Existing in-memory synthetic preview dictionary only. No real terrain, GIS, or JSON-file input is used.

## Method

Invoke table stdout and file modes, row limiting, overwrite protection, forced overwrite, path failures, output-selector conflicts, formatter failures, and existing CLI modes.

## Expected Result

Table modes reuse established formatter and file policies while preserving existing preview text and JSON behaviors.

## Actual Result

Focused and repository-wide tests passed locally. Manual table stdout and temporary file smoke completed without leaving a repository artifact.

## Metrics

- New output selectors: 2
- Total mutually exclusive output selectors: 5
- Status meanings preserved: 4
- Formatter behavior changes: 0
- Generated files committed: 0

## CI / Local Test Result

Local compile, pytest, Ruff, mypy, diff checks, and manual smoke are recorded in the Task 025B PR. GitHub Actions CI completed successfully for PR #68 on the checked head commit.

## Interpretation

The reviewed appendix-table projection is available through a narrow synthetic CLI surface without becoming a report, UI, or terrain integration layer.

## Limitations

The command remains synthetic-only. It does not validate MGRS geographic accuracy or field outcomes.

## Public Repository Sensitivity Check

No private path, terrain raster, generated table, JSON/TXT/CSV/PDF/image, report, QGIS project, or archive is committed.
