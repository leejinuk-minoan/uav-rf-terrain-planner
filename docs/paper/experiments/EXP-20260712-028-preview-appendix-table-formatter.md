# EXP-20260712-028 - Preview Appendix Table Formatter

## Experiment Purpose

Verify deterministic in-memory Markdown table formatting for the reviewed candidate preview contract.

## Input Data

Existing synthetic preview dictionaries only. No real terrain, file input, or GIS data is used.

## Method

Format valid and invalid mappings, inspect column order and record order, verify display-only row numbering, MGRS and source-zone metadata, score preservation, text-cell normalization, row limiting, immutability, and no-file behavior.

## Expected Result

The formatter returns a deterministic string and rejects contract violations without changing any existing preview or analysis layer.

## Actual Result

Focused and repository-wide tests passed locally. Direct in-memory formatting produced the expected header, preserved rows, and omitted-row message without creating an artifact.

## Metrics

- Table columns: 11
- Derived fields: 1 (`row_no`)
- File outputs: 0
- Existing production modules modified: 0

## CI / Local Test Result

Local compile, pytest, Ruff, mypy, diff checks, and direct smoke are recorded in the Task 024B PR. CI is recorded after push.

## Interpretation

The reviewed preview mapping can be projected into an appendix-oriented table without sorting, rescoring, persistence, report generation, or UI coupling.

## Limitations

The result is a formatting projection, not a ranking or validated operational recommendation. Synthetic MGRS values are not geographically assessed.

## Public Repository Sensitivity Check

Only source, tests, and Markdown records are included. No private path, raster, generated table, JSON/TXT/CSV/PDF/image, report, QGIS project, or archive is committed.
