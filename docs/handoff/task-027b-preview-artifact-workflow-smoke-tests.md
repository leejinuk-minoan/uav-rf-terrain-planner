# Task 027B Preview Artifact Workflow Smoke Tests

## Purpose

Task 027B fixes the nine documented preview artifact workflow commands as focused regression smoke tests without changing source behavior.

## Coverage

The tests cover synthetic plain text, JSON stdout, explicit JSON, table stdout, explicit table, saved JSON reuse to stdout/file, three-row limiting, and explicit forced overwrite. JSON validity, table metadata, MGRS fields, internal-coordinate exclusion, overwrite protection, and artifact containment are checked.

## Artifact policy

All runtime JSON and table artifacts use pytest `tmp_path`. No generated JSON, Markdown, text, data, image, or report artifact is committed.

## Verification

Focused smoke tests and the full local suite passed. Compileall, Ruff, mypy, diff, source-path, protected-path, GIS, `METADATA_MAP`, private-path, and generated-file checks were also run. CI passed on the reviewed PR head.

## Overall status

**passed locally and in CI on the reviewed PR head**.

## Limitations

The smoke suite validates the current synthetic preview artifact workflow only. It does not assess MGRS geographic accuracy or real terrain behavior.
