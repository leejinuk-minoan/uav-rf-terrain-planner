# EXP-20260711-023 - Preview CLI Scaffold

## Experiment Purpose

Verify a minimal stdout-only CLI for the existing synthetic MGRS candidate display preview.

## Input Data

Existing in-memory synthetic candidate preview smoke output only. No real terrain, `METADATA_MAP`, GIS file, or generated input file is used.

## Method

Invoke `build_synthetic_candidate_preview_smoke()` through a module CLI. Print its existing plain-text preview by default, optionally limit visible rows, or serialize its existing JSON-ready dictionary to stdout. Capture stdout/stderr and verify no files are created.

## Expected Result

- Default text output contains the preview title and MGRS field policy.
- A positive record limit truncates visible text rows and reports omissions.
- Invalid limits return non-zero status with concise stderr.
- JSON output parses and preserves `external_coordinate_format` and `candidate_cell_mgrs`.
- Internal/debug coordinates and file output remain absent.

## Actual Result

All three manual CLI commands completed successfully. Plain text displayed the existing five-record synthetic preview, the limited mode displayed three rows and reported two omissions, and JSON mode produced a valid complete preview dictionary. No file was created.

## Metrics

- CLI output modes: 2, plain text and JSON
- Default preview records: 5
- Limited visible records: 3
- Reported omitted records: 2
- Focused CLI tests: 13
- Successful status code: 0
- Expected preview-error status: 1
- Parser-error status: 2
- Generated files: 0

## CI / Local Test Result

Local compile, full pytest, Ruff, mypy, diff checks, focused tests, and manual CLI smoke results are recorded in the Task 022B PR. The CLI is synthetic-only and requires no local raster in CI.

## Interpretation

The existing preview contracts can be exposed through a small stdout adapter without introducing persistent-output, rendering, coordinate-conversion, or scoring behavior.

## Limitations

Synthetic placeholder MGRS values are not geographically validated. JSON output uses the complete existing dictionary, while `--max-records` limits plain text only. The CLI is not a report or UI surface.

## Figure/Table Candidacy

The CLI contract and status-code table may support implementation documentation. No screenshot or generated preview artifact is committed.

## Public Repository Sensitivity Check

Only synthetic in-memory values and repository-relative module references are documented. No private path, raster, generated file, CSV, PDF, image, QGIS project, or archive is included.

## Follow-up Tasks

Consider persistent JSON/text output only in a separate task with explicit path, overwrite, encoding, and repository-exclusion policies.
