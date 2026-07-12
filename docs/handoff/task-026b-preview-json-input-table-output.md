# Task 026B Preview JSON Input Table Output

## Purpose

Task 026B adds `--input-json PATH` as an explicit saved-preview source for table stdout and explicit table-file output.

## Implemented behavior

- Requires exactly one source: `--synthetic` or `--input-json PATH`.
- Allows saved input only with `--table` or `--output-table PATH`.
- Reads one explicit UTF-8 JSON file and requires an object top level.
- Reuses the existing appendix-table formatter for schema, MGRS, and internal-coordinate validation.
- Reuses `--max-records`, the explicit text writer, and `--force` overwrite policy.
- Avoids synthetic generation in saved-input mode.

## Error and status boundary

Input read/decode/top-level and formatter errors return status 1 without partial output. Source or output argument errors return status 2. Output path/write failures remain status 3. Input or formatter failure occurs before table-file writing, so an existing output is not replaced.

## Unchanged boundaries

Existing synthetic commands remain compatible. No JSON copying, preview-text reconstruction, automatic discovery, report/UI/HTML output, terrain/GIS access, MGRS conversion, sorting, ranking, rescoring, or control output is added.

## Verification

Focused and full tests, compileall, Ruff, mypy, diff checks, saved-input stdout/file smoke, cleanup, and protected-path checks are recorded in the Task 026B PR.

## Overall status

**passed locally, pending CI at initial handoff creation**.
