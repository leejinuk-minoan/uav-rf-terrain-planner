# Task 034C Diagnostic Appendix Table Delivery Boundary

## Purpose

Define a backward-compatible user-facing delivery contract for the Task 034B diagnostic appendix formatter without implementing source, tests, report, CLI, scoring, routing, or UI changes.

## Start Gate

Verified before branch creation:

```text
repository: leejinuk-minoan/uav-rf-terrain-planner
PR #91: closed / merged
PR #91 merge commit: 566de7de1eca2dc0e4771eca8e158772569d3d3d
Issue #90: closed / completed
Issue #92: open
base main SHA: 566de7de1eca2dc0e4771eca8e158772569d3d3d
open PRs: none
related open diagnostic-table issue: #92
```

Task 034B implementation and EXP-20260714-048 were verified on `main`.

## Branch and Draft PR

```text
branch: agent/task-034c-diagnostic-table-delivery-contract
Draft PR: #93
PR title: docs: define diagnostic table delivery boundary
PR state: open / draft / unmerged
initial documentation head: 4b4f6f5f8221ed5da2c5908775be879d5126e134
```

The Draft PR includes `Closes #92` and remains Draft until explicit user approval.

## Current Code Audit

### Diagnostic formatter

Implemented in:

```text
src/uav_rf_terrain/preview_appendix_table.py
```

API:

```python
format_fresnel_diagnostics_appendix_table(
    preview,
    *,
    max_rows=None,
)
```

The formatter returns the reviewed 14-column Markdown string and has no file I/O.

### Report

`format_preview_report(...)` already contains a narrative `## Fresnel Diagnostics` section and the existing `## Appendix Table` with the default 11-column table. It does not include the 14-column diagnostic table.

### CLI

The CLI currently provides synthetic and saved JSON sources, mutually exclusive output selectors, explicit UTF-8 text/file helpers, force overwrite protection, and status codes 0/1/2/3. It has no diagnostic-table selectors.

### Saved JSON

`--input-json PATH` exists. It currently requires table or report output. The saved preview dictionary is compatible with the diagnostic formatter's legacy, eligible, and no-eligible states.

## Alternatives Reviewed

```text
A. Python API-only
B. automatic report insertion
C. report opt-in
D. CLI stdout
E. CLI file output
F. staged CLI stdout/file, later report review
```

Recommendation: Alternative F.

Rationale:

- preserves every current default output and report snapshot;
- exposes the already stable formatter without duplicating its logic;
- reuses the existing CLI selector, max-record, file, encoding, overwrite, and exit-status boundaries;
- postpones the wider report composition decision, where duplication and document length require separate review.

## Selected Task 034D Contract

### New output selectors

```text
--diagnostic-table
--output-diagnostic-table PATH
```

Both are opt-in. They join the existing output-selector mutual-exclusion group. No implicit output precedence is allowed.

### Sources

Both new selectors support:

```text
--synthetic
--input-json PATH
```

Exactly one source remains required.

### Row limit

Reuse:

```text
--max-records N
```

For both new selectors:

```text
max_rows = args.max_records
```

No new limit option is added.

### Stdout/file equality

For identical source and limit:

```text
diagnostic stdout bytes == diagnostic file bytes
```

Both contain exactly one trailing newline. File encoding is UTF-8.

### File policy

Reuse `_write_text_output(...)`:

```text
no parent creation
directory path rejected
existing target rejected without --force
--force permits overwrite
success message: preview saved: <PATH>
```

Formatting occurs before target write. Input or diagnostic failures must not create, truncate, or replace the target.

### Errors

```text
parser/option error: status 2
input JSON error: status 1
diagnostic formatter error: status 1
file/path/write error: status 3
success: status 0
```

Diagnostic error stderr prefix:

```text
preview diagnostic table error:
```

### Report

Task 034D does not change report code or output. Report composition remains a later reviewed task.

## Documents Changed

New:

```text
docs/architecture/diagnostic-appendix-table-delivery-boundary.md
docs/handoff/task-034c-diagnostic-appendix-table-delivery-boundary.md
docs/paper/decisions/DEC-20260714-004-diagnostic-appendix-table-delivery-policy.md
docs/paper/experiments/EXP-20260714-049-diagnostic-appendix-table-delivery-contract-audit.md
```

Updated:

```text
docs/paper/decisions/README.md
docs/paper/experiments/README.md
docs/architecture/dominant-obstacle-appendix-table-output-boundary.md
docs/research/research-index.md
```

## Protected Paths

Task 034C does not modify:

```text
src/
tests/
.github/workflows/
pyproject.toml
lock files
```

It does not implement new CLI options, file output, report composition, runtime formatter changes, scoring, color, ranking, route, waypoint, map, or UI behavior.

## Task 034D Candidate Scope

Expected source:

```text
src/uav_rf_terrain/preview_cli.py
```

Preferred new focused test:

```text
tests/test_diagnostic_appendix_cli_output.py
```

Narrow regression additions may be made to existing CLI test files. `preview_appendix_table.py` and `preview_report.py` should remain unchanged unless a concrete blocker is demonstrated before scope expansion.

## Test Matrix

```text
existing CLI regression
new stdout/file selectors
synthetic and saved JSON sources
stdout/file equality
UTF-8 and one trailing newline
all selector conflicts
max-records propagation
legacy/eligible/no-eligible states
invalid diagnostics
status 1/2/3 mapping
file overwrite and path policy
no deterministic partial artifact
MGRS/internal-coordinate boundary
report unchanged
JSON/plain text/default table unchanged
scoring/routing/UI unchanged
```

## GitHub Actions Evidence

Initial Draft PR documentation head:

```text
run: CI #815
head: 4b4f6f5f8221ed5da2c5908775be879d5126e134
status: completed
conclusion: success
steps: install, syntax check, pytest, Ruff, mypy successful
```

The current PR body and Task completion report record the latest final-head GitHub Actions result. This durable handoff does not append a self-referential CI statement after each evidence-only amendment.

## Local Execution Claims

The Cloud Execution Agent did not execute compileall, pytest, Ruff, mypy, CLI commands, formatter output generation, rasterio, GDAL, or QGIS.

Task 034B local results remain attributed to the Local Execution Agent. Task 034C reports GitHub Actions evidence only.

## Limitations

This is a code/document contract audit. It is not runtime execution, local test evidence, RF validation, full link-budget validation, or communication, reconnaissance, or flight outcome evidence.

## Public Repository Sensitivity Check

The documents contain public repository metadata and interface contracts only. They add no generated artifact, GIS/DEM/DSM content, `METADATA_MAP` data, credential, private path, operational instruction, device command, autopilot command, or flight-control output.
