# Task 024B Preview Appendix Table Formatter

## Purpose

Task 024B adds a pure Python formatter that converts the reviewed in-memory preview dictionary into a deterministic Markdown pipe-table string.

## Implemented behavior

- Validates required top-level and record fields.
- Preserves input record order and derives one-based display-only `row_no` values.
- Displays MGRS candidate coordinates, existing score values, color fields, source-zone interpretation metadata, and candidate reasons.
- Rejects internal/debug coordinate keys.
- Normalizes cell line breaks and escapes pipe characters.
- Supports optional positive `max_rows` and a deterministic omitted-row line.
- Does not mutate input or create files.

## Unchanged boundaries

No CLI option, existing preview schema, existing preview text, file-output behavior, scoring, LOS/Fresnel, route, waypoint, terrain, report, UI, HTML, or MGRS conversion behavior is changed.

## Verification

Local focused tests, full pytest, compileall, Ruff, mypy, diff checks, protected-path checks, and an in-memory formatter smoke are recorded in the Task 024B PR.

## Overall status

**passed locally and in GitHub Actions CI for PR #66 on the checked head commit**.

## Limitations

The formatter consumes synthetic reviewed preview mappings. It does not assess MGRS geographic accuracy, real terrain, or operational outcomes.

## Public repository sensitivity check

No private path, sensitive coordinate, GIS data, generated table, JSON/TXT/CSV/PDF/image, report, or QGIS artifact is committed.
