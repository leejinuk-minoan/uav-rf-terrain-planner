# Task 025B Preview Table CLI Output

## Purpose

Task 025B connects the existing appendix-table formatter to the synthetic preview CLI through `--table` and explicit `--output-table PATH` modes.

## Implemented behavior

- `--table` prints the existing formatter string to stdout.
- `--output-table PATH` reuses the existing UTF-8 text writer and explicit-path policy.
- `--max-records` is passed to the formatter as `max_rows`.
- `--force` reuses existing overwrite behavior for table files.
- All five output selectors are mutually exclusive.
- Formatter errors return status 1, argument conflicts status 2, and file errors status 3.

## Compatibility

Default preview text, JSON stdout, JSON files, and preview text files retain their existing behavior. The appendix formatter and preview schemas are unchanged.

## Boundaries

No JSON-file input, automatic directory creation, report/UI/HTML output, terrain access, GIS dependency, MGRS conversion, sorting, ranking, rescoring, or vehicle-control behavior is added. Generated table files are temporary runtime artifacts and are not committed.

## Verification

Focused and full tests, compileall, Ruff, mypy, diff checks, manual table stdout, limited table stdout, and temporary table-file smoke results are recorded in the Task 025B PR.

## Overall status

**passed locally and in GitHub Actions CI for PR #68 on the checked head commit**.
