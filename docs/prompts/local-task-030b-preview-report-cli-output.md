# Local Task 030B - Preview Report CLI Output

## Role

You are a Local Execution Agent for the UAV RF Terrain Planner repository. Implement and verify only the approved preview report stdout and explicit report-file CLI integration.

Do not expand the task into formatter redesign, schema changes, GIS, terrain, scoring, route, waypoint, UI, rendered artifacts, or external-device behavior.

## Repository

```text
leejinuk-minoan/uav-rf-terrain-planner
```

## Branch

Base branch:

```text
main
```

New branch:

```text
agent/task-030b-preview-report-cli-output
```

Create the branch only after Task 030A has been merged. Use the Task 030A merge commit as the exact base.

## Base Commit Placeholder

```text
TASK_030A_MERGE_COMMIT_TO_BE_FILLED_BY_GPT_MASTER
```

Do not assume the placeholder. Confirm the current `main` commit before editing and report the exact base SHA.

## Required Files to Read

Read these files before implementation:

```text
README.md
AGENTS.md
CLAUDE.md
docs/architecture/preview-documentation-reconciliation.md
docs/architecture/preview-artifact-workflow.md
docs/usage/preview-artifact-workflow.md
docs/architecture/preview-cli-output-contract.md
docs/architecture/preview-report-boundary-plan.md
docs/architecture/preview-report-cli-output-boundary-plan.md
docs/architecture/current-candidate-preview-pipeline.md
src/uav_rf_terrain/preview_cli.py
src/uav_rf_terrain/preview_appendix_table.py
src/uav_rf_terrain/preview_report.py
tests/test_preview_cli.py
tests/test_preview_cli_contract.py
tests/test_preview_table_cli_output.py
tests/test_preview_json_input_table_output.py
tests/test_preview_artifact_workflow_smoke.py
tests/test_preview_report.py
docs/handoff/task-029b-preview-report-formatter.md
docs/handoff/task-030a-preview-report-cli-output-boundary-plan.md
docs/paper/experiments/EXP-20260712-037-preview-report-formatter.md
docs/paper/experiments/EXP-20260712-038-preview-report-cli-output-boundary-plan.md
docs/paper/experiments/README.md
```

If the current source or tests conflict with the Task 030A boundary, stop implementation and report the exact conflict.

## Objective

Connect the existing pure `format_preview_report(...)` formatter to the preview CLI through:

```text
--report
--output-report PATH
```

Support report stdout and explicit report-file output for both the synthetic source and saved preview JSON source while preserving every existing CLI mode.

## Implementation Scope

Modify:

```text
src/uav_rf_terrain/preview_cli.py
```

Add:

```text
tests/test_preview_report_cli_output.py
docs/handoff/task-030b-preview-report-cli-output.md
docs/paper/experiments/EXP-20260712-039-preview-report-cli-output.md
```

Update once:

```text
docs/paper/experiments/README.md
```

A concise README Task 030B sentence may be added only if it follows the existing task-summary style. Do not broaden README changes.

## CLI Option Additions

Add output selectors:

```text
--report
--output-report PATH
```

Recommended parser shape:

```python
parser.add_argument(
    "--report",
    action="store_true",
    dest="report_output",
    help="print the existing preview as a human-readable report",
)
parser.add_argument("--output-report", metavar="PATH")
```

Both options are output selectors. Add them to the existing mutual-exclusion count in `_validate_arguments(...)`.

Do not rename or remove existing options.

## Source and Output Compatibility

Required report compatibility:

| Source | `--report` | `--output-report PATH` |
|---|---:|---:|
| `--synthetic` | Allowed | Allowed |
| `--input-json PATH` | Allowed | Allowed |

Preserve:

- exactly one source selector;
- at most one output selector;
- synthetic input with no output selector remains plain-text stdout;
- saved JSON remains supported for table stdout and table file;
- saved JSON becomes supported for report stdout and report file;
- saved JSON remains unsupported for JSON stdout, JSON file, and plain-text file;
- bare saved JSON input remains an argument error.

## Report Stdout Behavior

For `--report`:

1. obtain the preview dictionary through the selected existing source path;
2. call `format_preview_report(preview_dict)` exactly once;
3. write the returned string to stdout;
4. create no file;
5. emit no stderr on success.

The current formatter returns exactly one trailing newline. Do not call plain `print(report_text)` because that would add another newline.

Use behavior equivalent to:

```python
print(report_text, end="")
```

Tests must verify one terminal newline and no double newline.

## Report File-Output Behavior

For `--output-report PATH`:

1. obtain and validate the preview dictionary;
2. call `format_preview_report(preview_dict)` exactly once;
3. complete report formatting before any write;
4. use the existing `_write_text_output(...)` helper;
5. preserve UTF-8 and one trailing newline;
6. preserve the existing `--force` policy;
7. print the existing confirmation style:

```text
preview saved: <PATH>
```

Do not create parent directories. Do not alter `_write_text_output(...)` unless a proven bug blocks this task; report such a conflict before broadening scope.

## Formatter Integration

Import:

```python
from .preview_report import PreviewReportError, format_preview_report
```

Recommended control flow:

- retain `preview_text` for existing synthetic plain-text modes;
- retain `table_text` for existing table modes;
- introduce a separate `report_text: str | None`;
- generate `report_text` only when `--report` or `--output-report` is selected;
- catch `PreviewReportError` and return status 1;
- use the formatter default `include_table=True`;
- do not call `format_preview_appendix_table(...)` directly for report mode;
- do not change `preview_report.py`.

Recommended handled message:

```text
preview report error: <message>
```

## Argument Validation

Extend `_validate_arguments(...)` so that:

- `--report` conflicts with every existing output selector and `--output-report`;
- `--output-report` conflicts with every existing output selector;
- saved input supports table stdout, table file, report stdout, or report file only;
- `--max-records` with report stdout or report file is rejected as an argument error;
- the existing behavior of `--force` outside explicit file-output modes is not changed.

Expected status 2 cases include:

```text
--synthetic --report --table
--synthetic --report --json
--synthetic --report --output-text PATH
--synthetic --output-report PATH --output-table OTHER
--input-json PATH
--input-json PATH --json
--input-json PATH --output-json OTHER
--input-json PATH --output-text OTHER
--synthetic --report --max-records 3
--input-json PATH --output-report REPORT --max-records 3
```

## Error and Status Handling

Preserve status meanings:

```text
0 = success
1 = handled preview/input/formatter error
2 = parser / argument error
3 = handled output-file error
```

Required mapping:

- successful report stdout or file: 0;
- saved JSON read/decode/top-level error: 1;
- `PreviewReportError`: 1;
- source/output conflict: 2;
- unsupported saved-input output combination: 2;
- report combined with `--max-records`: 2;
- missing parent, directory target, protected existing file, or write failure: 3.

Invalid input or formatter failure must occur before `_write_text_output(...)`, so the selected file is not created, truncated, or replaced.

## Coordinate and Metadata Boundary

Report output must preserve:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
source_zone
source_sensitive
source_zone_reason
```

Internal/debug names must remain excluded:

```text
x_m
y_m
row
col
epsg5179_x_m
epsg5179_y_m
wgs84_lat
wgs84_lon
local_x_m
local_y_m
raster_row
raster_col
```

Do not add coordinate conversion, geographic validation, scoring changes, record reordering, route changes, or waypoint changes.

## Tests Required

Add focused tests covering at least:

1. `--synthetic --report` returns 0;
2. synthetic report stdout contains expected headings;
3. report stdout ends with one newline and not two;
4. `--synthetic --output-report PATH` writes UTF-8 report text;
5. report-file success prints the existing save confirmation;
6. `--input-json PATH --report` uses saved preview JSON;
7. `--input-json PATH --output-report PATH` writes a report;
8. each report selector conflicts with every other output selector;
9. bare saved JSON input remains rejected;
10. saved JSON with JSON stdout, JSON file, or plain-text file remains rejected;
11. `--max-records` with either report selector returns status 2;
12. report output includes MGRS and candidate coordinates;
13. report output excludes internal/debug coordinate names;
14. invalid saved JSON report returns status 1;
15. a monkeypatched `PreviewReportError` returns status 1 with concise stderr;
16. missing parent returns status 3;
17. directory target returns status 3;
18. an existing report file is protected without `--force`;
19. `--force` allows overwrite;
20. invalid preview input does not create a new report file;
21. invalid preview input does not replace an existing report file;
22. existing preview CLI, table, saved-input, artifact-workflow, and report formatter tests remain unchanged and pass;
23. no generated report artifact is committed.

Use `tmp_path` for all JSON and report files created by tests.

## Forbidden Changes

Do not change:

```text
src/uav_rf_terrain/preview_report.py
src/uav_rf_terrain/preview_appendix_table.py
tests/test_preview_report.py
tests/test_preview_appendix_table.py
tests/test_preview_cli.py
tests/test_preview_cli_contract.py
tests/test_preview_table_cli_output.py
tests/test_preview_json_input_table_output.py
tests/test_preview_artifact_workflow_smoke.py
pyproject.toml
.github/workflows/ci.yml
docs/deployment/android-tmmr-offline-plan.md
```

Do not add:

- report row-limit behavior;
- an appendix-table exclusion CLI option;
- report-specific schema fields;
- a new file writer or output directory policy;
- generated sample reports;
- HTML, PDF, image, map, card, popup, or interactive rendering;
- real terrain or `METADATA_MAP` access;
- GIS dependencies;
- coordinate conversion or geographic validation;
- field RF measurement validation;
- candidate rescoring, reranking, or exclusion;
- LOS/Fresnel recalculation;
- route or waypoint changes;
- external-device or flight-control behavior;
- CI runner, matrix, cache, artifact upload, Git LFS, package upload, release asset, or large-data changes.

Do not commit raster, QGIS, archive, image, PDF, CSV, generated JSON, generated text, or generated report files.

## Verification Commands

Run locally:

```bash
python -m compileall src tests examples scripts
python -m pytest tests/test_preview_report_cli_output.py tests/test_preview_report.py
python -m pytest
python -m ruff check .
python -m mypy src
git diff --check
git status --short
git diff --name-only
```

Run scope checks:

```bash
git diff --name-only | grep -E '^(src/uav_rf_terrain/preview_report.py|src/uav_rf_terrain/preview_appendix_table.py|tests/test_preview_report.py|tests/test_preview_appendix_table.py|tests/test_preview_cli.py|tests/test_preview_cli_contract.py|tests/test_preview_table_cli_output.py|tests/test_preview_json_input_table_output.py|tests/test_preview_artifact_workflow_smoke.py)$' && echo "FORBIDDEN EXISTING FILE CHANGED" || true

git diff --name-only | grep -E '^(\.github/workflows/ci.yml|pyproject.toml|docs/deployment/android-tmmr-offline-plan.md)$' && echo "FORBIDDEN PROTECTED PATH CHANGED" || true

git diff --name-only | grep -E '\.(tif|tiff|img|vrt|zip|aux\.xml|ovr|qgz|qgs|png|jpg|jpeg|webp|svg|csv|pdf|json|txt)$' && echo "FORBIDDEN DATA OR GENERATED FILE COMMITTED" || true

git diff --name-only | grep '^METADATA_MAP/' && echo "METADATA_MAP FILE COMMITTED" || true

grep -nE 'C:\\Users|/Users/|/home/|file://' -R README.md docs || true
```

Run representative CLI smoke commands using a temporary directory. Do not commit their output:

```bash
python -m uav_rf_terrain.preview_cli --synthetic --report
python -m uav_rf_terrain.preview_cli --synthetic --output-report <TEMP_REPORT_PATH>
```

## Commit and Push

Commit message:

```text
feat: add preview report cli output
```

Push only the Task 030B branch. Do not merge.

## PR Body

```markdown
## Purpose

Add report stdout and explicit report-file output to the existing preview CLI.

## Implemented

- Added `--report`.
- Added `--output-report PATH`.
- Connected the existing pure report formatter.
- Added synthetic and saved-JSON report output.
- Preserved existing output-selector, file-protection, and status-code behavior.
- Added focused tests, handoff documentation, and experiment record.

## Not Included

- No report formatter changes.
- No preview schema or field changes.
- No table formatter changes.
- No report row-limit option.
- No appendix-table exclusion CLI option.
- No GIS, terrain, coordinate-conversion, scoring, route, waypoint, UI, or external-device changes.
- No generated report artifact committed.

## Verification

- `python -m compileall src tests examples scripts`
- focused report CLI tests
- full `python -m pytest`
- `python -m ruff check .`
- `python -m mypy src`
- `git diff --check`
- GitHub Actions CI: <pending/success>
```

## Completion Report Format

```text
Task:
Branch:
PR:
Base commit:
Commit:
Changed files:
CLI options added:
Source/output compatibility:
Report stdout behavior:
Report file-output behavior:
Formatter integration:
Argument validation:
Status/error mapping:
Coordinate/metadata boundary:
Mutation/artifact check:
Existing-mode regression check:
Protected file check:
GIS/METADATA_MAP/generated-file check:
Commands run:
Focused tests:
Full tests:
Ruff:
Mypy:
Compileall:
CLI smoke:
CI:
Limitations:
Ready for GPT Master review:
```

Do not claim command or CI success unless the corresponding execution actually completed successfully.
