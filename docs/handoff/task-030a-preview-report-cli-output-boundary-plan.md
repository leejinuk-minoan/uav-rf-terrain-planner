# Task 030A Preview Report CLI Output Boundary Plan

## Purpose

Task 030A defines the planned boundary for connecting the existing pure preview report formatter to report stdout and explicit report-file output.

This task is documentation only. It does not implement CLI options, generate reports, write report files, modify formatter behavior, or change the preview schema.

## Documents Added

- `docs/architecture/preview-report-cli-output-boundary-plan.md`
- `docs/prompts/local-task-030b-preview-report-cli-output.md`
- `docs/handoff/task-030a-preview-report-cli-output-boundary-plan.md`
- `docs/paper/experiments/EXP-20260712-038-preview-report-cli-output-boundary-plan.md`

The experiment index receives one EXP-20260712-038 entry.

README is intentionally unchanged because the requested Task 030A sentence is optional and the narrower five-path documentation diff is sufficient.

## Proposed CLI Surface

Task 030B may add:

```text
--report
--output-report PATH
```

Both are output selectors. They conflict with all existing output selectors. Existing default plain-text, JSON, text-file, table, and saved-input table behavior remains unchanged.

`--output-text` continues to mean the existing plain preview-text file. It is not reused for report output.

## Source and Output Compatibility

Required report compatibility:

| Source | Report stdout | Report file |
|---|---:|---:|
| Synthetic preview | Allowed | Allowed |
| Saved preview JSON | Allowed | Allowed |

Saved JSON remains unsupported for JSON stdout, JSON file, and plain preview-text file. Bare saved JSON input remains an argument error.

Exactly one source selector and at most one output selector remain mandatory.

## Report Stdout Boundary

Task 030B should obtain one preview dictionary, call `format_preview_report(preview_dict)` once, and write the returned string to stdout.

The current formatter returns exactly one trailing newline. CLI integration must not add a second newline. The planned behavior is equivalent to:

```python
print(report_text, end="")
```

Report stdout creates no file and emits no stderr on success.

## Report File-Output Boundary

`--output-report PATH` writes the existing report string to one explicit UTF-8 path through the existing text-output helper.

Policy remains:

- no automatic parent-directory creation;
- missing parent, directory target, protected existing file, or write failure returns status 3;
- overwrite requires `--force`;
- formatter validation completes before any write;
- successful output retains `preview saved: <PATH>` confirmation style;
- invalid input does not create, truncate, or replace a report file.

## Formatter Integration Boundary

Task 030B may import:

```text
PreviewReportError
format_preview_report
```

Synthetic mode uses the existing synthetic preview dictionary. Saved-input mode uses the existing decoded JSON mapping.

Report mode uses the formatter default `include_table=True`. It does not call the table formatter separately and does not change `preview_report.py`.

## Argument Validation Boundary

Task 030B must:

- add both report selectors to the output-selector count;
- reject either report selector combined with any other output selector;
- allow saved input with table or report output only;
- reject report output combined with `--max-records` as status 2;
- leave the current behavior of `--force` outside explicit file modes unchanged.

The report row-limit boundary is intentionally deferred because the report summary and embedded table must remain internally consistent.

## Status and Error Boundary

Existing status meanings remain:

```text
0 = success
1 = handled preview/input/formatter error
2 = parser / argument error
3 = handled output-file error
```

`PreviewReportError` maps to status 1. Report selector conflicts and report plus `--max-records` map to status 2. Explicit report-file errors map to status 3.

Handled report errors should use concise stderr without a traceback.

## Coordinate and Metadata Boundary

Report CLI output preserves:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
source_zone
source_sensitive
source_zone_reason
```

Internal local/projected/raster coordinates remain excluded. Task 030B performs no coordinate conversion, geographic validation, score recalculation, record reorder, route change, or waypoint change.

Source-zone fields remain interpretation metadata and do not become a suitability decision or measured link-quality result.

## Artifact Handling Boundary

Report-file output is limited to one explicit path selected by the user.

Task 030B adds no default report directory, path discovery, parent creation, sample report, Actions artifact, Git LFS object, package upload, release asset, GIS file, raster, QGIS project, PDF, image, CSV, or generated repository artifact.

Tests use temporary paths only.

## Task 030B Scope

Recommended branch:

```text
agent/task-030b-preview-report-cli-output
```

Recommended changed files:

```text
src/uav_rf_terrain/preview_cli.py
tests/test_preview_report_cli_output.py
docs/handoff/task-030b-preview-report-cli-output.md
docs/paper/experiments/EXP-20260712-039-preview-report-cli-output.md
docs/paper/experiments/README.md
```

Task 030B should add report stdout/file options, integrate the existing formatter, support both existing sources, preserve current modes and file policy, and add focused tests.

## Code/Test Change Check

- Source files changed by Task 030A: 0
- Test files changed by Task 030A: 0
- CLI options implemented: 0
- Formatter behavior changes: 0
- Preview schema changes: 0
- Preview field changes: 0
- Existing file-output behavior changes: 0
- Generated runtime artifacts committed: 0

## Test/CI Result

The Cloud Agent does not claim local compileall, pytest, Ruff, mypy, CLI execution, JSON read/write, report generation, or report-file output for this documentation-only task.

GitHub Actions is checked on the final PR head. The CI workflow, runner, matrix, cache, and artifact policy remain unchanged.

## Overall Status

The report workflow is separated into reviewed stages:

1. Task 029A: pure formatter boundary plan;
2. Task 029B: pure formatter implementation;
3. Task 030A: CLI stdout/file-output boundary plan;
4. Task 030B: narrow Local CLI integration.

This preserves the existing preview contract while adding a controlled future report output surface.

## Limitations

Task 030A does not execute the CLI or formatter. It does not inspect generated report output, validate actual MGRS geography, access terrain data, evaluate field RF conditions, modify scoring, or add a rendered application surface.

The plan relies on the implemented Task 029B contract that the report formatter returns one trailing newline and validates through the appendix-table boundary.

## Public Repository Sensitivity Check

Only repository Markdown documentation and one experiment-index entry are included. No private path, credential, raster, GIS data, `METADATA_MAP` content, generated JSON/text/report artifact, QGIS project, CSV, PDF, image, or archive is included.

The documentation remains within research, education, simulation, and human-review boundaries.

## Follow-Up Tasks

1. Merge Task 030A only after GPT Master review and successful CI on the final head.
2. Replace the Task 030B base-commit placeholder with the Task 030A merge commit.
3. Run Task 030B as a narrow Local implementation and verification task.
4. Reconcile workflow and usage documentation only after Task 030B is merged.
5. Keep UI, rendered artifacts, and real-terrain integration separate.
