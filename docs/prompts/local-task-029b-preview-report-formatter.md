# Local Task 029B - Preview Report Formatter

## Role

You are a Local Execution Agent for the UAV RF Terrain Planner repository. Implement and verify one narrow pure-Python preview report formatter. Do not expand the task into CLI, file-output, GIS, terrain, scoring, route, waypoint, UI, or rendered-artifact work.

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
agent/task-029b-preview-report-formatter
```

Create the branch only after Task 029A has been merged. Use the Task 029A merge commit as the base.

## Base Commit Placeholder

```text
TASK_029A_MERGE_COMMIT_TO_BE_FILLED_BY_GPT_MASTER
```

Do not assume the placeholder value. Confirm `main` and record the actual base commit before editing.

## Required Files to Read

Read these files before implementation:

```text
README.md
AGENTS.md
CLAUDE.md
docs/architecture/preview-documentation-reconciliation.md
docs/architecture/preview-artifact-workflow.md
docs/architecture/preview-report-boundary-plan.md
docs/architecture/preview-cli-output-contract.md
docs/architecture/current-candidate-preview-pipeline.md
src/uav_rf_terrain/coordinate_io_policy.py
src/uav_rf_terrain/preview_appendix_table.py
src/uav_rf_terrain/preview_cli.py
src/uav_rf_terrain/synthetic_candidate_preview_smoke.py
tests/test_preview_appendix_table.py
tests/test_preview_cli_contract.py
tests/test_preview_artifact_workflow_smoke.py
docs/handoff/task-029a-preview-report-boundary-plan.md
docs/paper/experiments/EXP-20260712-036-preview-report-boundary-plan.md
docs/paper/experiments/README.md
```

If any file is missing or the implemented contract differs from the Task 029A plan, stop implementation and report the conflict.

## Objective

Add a pure formatter that converts an existing reviewed preview mapping into a deterministic human-readable Markdown/plain-text report string.

The task must not add report CLI options, read or write files, create artifacts, change the preview schema, alter appendix-table output, access terrain data, convert coordinates, recalculate scores, or change route/waypoint behavior.

## Implementation Scope

Add:

```text
src/uav_rf_terrain/preview_report.py
tests/test_preview_report.py
docs/handoff/task-029b-preview-report-formatter.md
docs/paper/experiments/EXP-20260712-037-preview-report-formatter.md
```

Update once:

```text
docs/paper/experiments/README.md
```

A concise README Task 029B sentence may be added if it follows the existing task-summary style. Do not broaden README changes.

## Proposed Module and Function

Implement:

```python
from collections.abc import Mapping

class PreviewReportError(ValueError):
    """Raised when preview input violates the report contract."""


def format_preview_report(
    preview: Mapping[str, object],
    *,
    include_table: bool = True,
) -> str:
    """Return a deterministic human-readable report without mutating input."""
```

The module must remain pure Python and must not import `pathlib`, `argparse`, `preview_cli`, GIS packages, rendering packages, or file-writing helpers.

## Proposed Sections

Use this exact order:

```text
# Preview Candidate Report

## Summary
## Source and Output Context
## Candidate Overview
## Source-Zone Interpretation
## Coordinate Boundary
## Appendix Table
## Limitations
```

When `include_table=False`, omit both the `## Appendix Table` heading and its content. Keep every other section in the same order.

### Summary

Include deterministic lines for:

```text
Record count
Source-sensitive count
External coordinate format
User coordinate field
```

Use existing input values only.

### Source and Output Context

State that the formatter consumes an existing preview mapping. Because the current preview schema does not encode whether the mapping came from the synthetic path or a saved JSON file, include a stable statement equivalent to:

```text
Input provenance: not encoded in preview
```

Do not infer provenance.

### Candidate Overview

Summarize:

- total candidate count;
- color class/name counts using a deterministic order;
- existing `overall_score` minimum and maximum;
- existing `shielding_stability_score` minimum and maximum.

Do not sort or mutate records. Do not recalculate scores. If a stable count order is needed, use first-seen record order or another explicitly tested deterministic rule.

### Source-Zone Interpretation

Explain and optionally summarize existing:

```text
source_zone
source_sensitive
source_zone_reason
```

These are interpretation metadata only. They do not change score, color, record order, LOS/Fresnel values, routes, or waypoints.

### Coordinate Boundary

Include:

```text
external_coordinate_format = MGRS
user_coordinate_field = candidate_cell_mgrs
```

Explain that existing MGRS text is displayed but not converted or geographically validated.

### Appendix Table

For `include_table=True`, call:

```python
format_preview_appendix_table(preview)
```

Insert its exact returned string without reformatting table columns, values, record order, or escaping.

Do not add a report row-limit argument in this task.

### Limitations

Include stable statements that the report:

- uses reviewed preview fields only;
- performs no coordinate conversion or geographic validation;
- performs no field RF measurement validation;
- performs no LOS/Fresnel recalculation;
- does not rescore or rerank candidates;
- does not alter route or waypoint results;
- is not an external-device or flight-control output.

Avoid outcome-assurance language.

## Input Contract

Reuse the existing appendix-table validation boundary. Current required top-level fields are:

```text
title
external_coordinate_format
user_coordinate_field
record_count
source_sensitive_count
records
summary
reason
```

Current required record fields are:

```text
candidate_id
candidate_cell_mgrs
external_coordinate_format
user_coordinate_field
color_class
color_name
overall_score
shielding_stability_score
source_zone
source_sensitive
source_zone_reason
candidate_reason
display_label
```

Requirements:

- no report-specific preview schema;
- no new preview fields;
- no field rename or removal;
- `record_count` must equal `len(records)`;
- records must remain non-empty;
- coordinate format must remain MGRS;
- user coordinate field must remain `candidate_cell_mgrs`;
- existing numeric and boolean checks remain effective;
- internal/debug coordinate keys remain rejected.

Internal/debug coordinate names include:

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

Preferred narrow implementation:

1. call `format_preview_appendix_table(preview)` once when `include_table=True` and use its successful validation/output;
2. when `include_table=False`, still validate through the existing preview/table contract without producing a file or changing table behavior;
3. catch `PreviewAppendixTableError` and raise `PreviewReportError` with exception chaining.

If validation reuse requires exposing a new public helper from `preview_appendix_table.py`, do not proceed automatically. Report the need to GPT Master because Task 029A assumes a narrow formatter addition, not an existing-module API refactor.

## Output Contract

Return one `str` with:

- deterministic heading and section order;
- UTF-8-safe text;
- stable labels and wording;
- no path or file behavior;
- no stdout/stderr printing;
- no HTML, image, PDF, map, card, popup, or interactive output.

Choose and test one terminal-newline policy. Do not couple it to current CLI file-output helpers.

## Error Handling

Use:

```text
PreviewReportError
```

Requirements:

- invalid preview structure or values raise `PreviewReportError`;
- appendix-table validation errors are translated to `PreviewReportError`;
- preserve the original exception as `__cause__`;
- return no partial report on failure;
- print nothing to stdout or stderr;
- add no process-status mapping.

## Tests Required

Add focused tests covering at least:

1. valid preview returns `str`;
2. exact section ordering;
3. summary includes record count, source-sensitive count, MGRS, and `candidate_cell_mgrs`;
4. source/output context states that provenance is not encoded;
5. candidate overview includes deterministic color counts and score ranges;
6. source-zone interpretation is present;
7. `include_table=True` includes the exact existing appendix-table string;
8. `include_table=False` omits the appendix-table heading and content;
9. candidate MGRS values may appear while internal/debug coordinate names do not;
10. invalid top-level and record inputs raise `PreviewReportError`;
11. original table validation error is exception-chained;
12. input mapping and nested records are unchanged after formatting;
13. no file or directory is created under `tmp_path`;
14. module source contains no GIS, CLI, rendering, path, or file-writing dependency;
15. existing appendix-table tests remain unchanged and pass;
16. full repository test suite passes.

Use the existing deterministic synthetic preview helper for test input. Do not commit generated report samples.

## Forbidden Changes

Do not change:

```text
src/uav_rf_terrain/preview_cli.py
tests/test_preview_cli.py
tests/test_preview_cli_contract.py
tests/test_preview_appendix_table.py
tests/test_preview_table_cli_output.py
tests/test_preview_json_input_table_output.py
tests/test_preview_artifact_workflow_smoke.py
pyproject.toml
.github/workflows/ci.yml
docs/deployment/android-tmmr-offline-plan.md
```

Do not add or implement:

- `--report`;
- `--output-report`;
- report file reading or writing;
- JSON input loading;
- default artifact directories;
- parent-directory creation or overwrite policy;
- sample/generated report artifacts;
- HTML, PDF, image, UI, map, card, or popup rendering;
- real DEM/DSM/landcover access;
- `METADATA_MAP` access;
- GIS dependencies;
- MGRS conversion or geographic accuracy validation;
- field RF measurement validation;
- candidate rescoring, sorting, reranking, or exclusion;
- LOS/Fresnel recalculation;
- route or waypoint changes;
- external-device, autopilot, or vehicle-command output;
- runner, matrix, cache, artifact-upload, Git LFS, package-upload, release-asset, or large-data CI changes.

Do not commit `.tif`, `.tiff`, `.img`, `.vrt`, `.zip`, `.aux.xml`, `.ovr`, `.qgz`, `.qgs`, `.png`, `.jpg`, `.jpeg`, `.webp`, `.svg`, `.csv`, `.pdf`, generated `.json`, or generated `.txt` files.

## Verification Commands

Run locally:

```bash
python -m compileall src tests examples scripts
python -m pytest
python -m ruff check .
python -m mypy src
git diff --check
git status --short
git diff --name-only
```

Run scope checks:

```bash
git diff --name-only | grep -E '^(src/uav_rf_terrain/preview_cli.py|tests/test_preview_cli.py|tests/test_preview_cli_contract.py|tests/test_preview_appendix_table.py|tests/test_preview_table_cli_output.py|tests/test_preview_json_input_table_output.py|tests/test_preview_artifact_workflow_smoke.py)$' && echo "FORBIDDEN EXISTING FILE CHANGED" || true

git diff --name-only | grep -E '^(.github/workflows/ci.yml|pyproject.toml|docs/deployment/android-tmmr-offline-plan.md)$' && echo "FORBIDDEN PROTECTED PATH CHANGED" || true

git diff --name-only | grep -E '\.(tif|tiff|img|vrt|zip|aux\.xml|ovr|qgz|qgs|png|jpg|jpeg|webp|svg|csv|pdf|json|txt)$' && echo "FORBIDDEN DATA OR GENERATED FILE COMMITTED" || true

git diff --name-only | grep '^METADATA_MAP/' && echo "METADATA_MAP FILE COMMITTED" || true

grep -nE 'C:\\Users|/Users/|/home/|file://' -R README.md docs || true
```

Run representative focused tests before the full suite:

```bash
python -m pytest tests/test_preview_report.py tests/test_preview_appendix_table.py
```

## Commit and Push

Commit message:

```text
feat: add pure preview report formatter
```

Push only the Task 029B branch. Do not merge.

## PR Body

```markdown
## Purpose

Add a pure deterministic formatter for a human-readable preview report.

## Implemented

- Added `PreviewReportError`.
- Added `format_preview_report(...)`.
- Added deterministic report sections and candidate summaries.
- Reused the existing preview/appendix-table validation boundary.
- Added optional appendix-table inclusion.
- Added focused tests, handoff documentation, and experiment record.

## Not Included

- No CLI changes.
- No report stdout or report-file output.
- No file read/write behavior.
- No preview schema or field changes.
- No appendix-table behavior changes.
- No GIS or terrain access.
- No coordinate conversion.
- No score, LOS/Fresnel, route, or waypoint changes.
- No UI or rendered artifacts.
- No external-device control output.

## Verification

- `python -m compileall src tests examples scripts`
- `python -m pytest`
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
Formatter module:
Public function:
Exception boundary:
Report sections:
Input contract reuse:
Candidate overview behavior:
Appendix table behavior:
Coordinate/metadata boundary:
Mutation check:
File/artifact check:
CLI change check:
Protected file check:
GIS/METADATA_MAP/generated-file check:
Commands run:
Focused tests:
Full tests:
Ruff:
Mypy:
Compileall:
CI:
Limitations:
Ready for GPT Master review:
```

Do not claim local or CI success unless the corresponding command or GitHub Actions run actually completed successfully.
