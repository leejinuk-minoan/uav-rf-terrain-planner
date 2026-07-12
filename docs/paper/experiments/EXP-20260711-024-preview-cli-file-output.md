# EXP-20260711-024 - Preview CLI Explicit File Output

## Experiment Purpose

Verify explicit UTF-8 JSON and plain-text persistence for the existing synthetic MGRS candidate preview while preserving stdout behavior and repository boundaries.

## Input Data

Existing in-memory synthetic candidate preview output only. No real terrain, `METADATA_MAP`, or GIS input is used.

## Method

Run the module CLI with explicit temporary output paths. Validate JSON parsing, text row limiting, overwrite protection, forced overwrite, missing-parent and directory-target failures, conflicting mode rejection, cleanup, and internal-coordinate exclusion.

## Expected Result

Only user-selected paths are written. Existing files require `--force`, parent directories are not created, JSON preserves MGRS fields, and text output reuses the existing formatter.

## Actual Result

Focused automated tests and manual smoke commands passed locally. Generated smoke files were removed and were not staged or committed.

## Metrics

- Explicit file formats: 2
- Success status: 0
- Preview generation error status: 1
- Parser error status: 2
- File-output error status: 3
- Automatic output directories created: 0

## CI / Local Test Result

Local compile, full pytest, Ruff, mypy, diff checks, and manual file-output smoke are recorded in the Task 022C PR. CI is recorded separately after push.

## Interpretation

The preview CLI can persist its existing MGRS-based inspection output without introducing report generation, rendering, terrain access, coordinate conversion, or scoring changes.

## Limitations

This is synthetic-only developer output. It does not validate MGRS geographic accuracy or field outcomes.

## Public Repository Sensitivity Check

No private path, generated preview, raster, CSV, PDF, image, QGIS project, or archive is committed.
