# Diagnostic Appendix Table Delivery Boundary

## Purpose

This document defines the reviewed delivery contract for exposing the already implemented pure Markdown formatter:

```python
format_fresnel_diagnostics_appendix_table(
    preview,
    *,
    max_rows=None,
)
```

Task 034C is a documentation and code-contract audit only. It does not change source code, tests, report composition, CLI behavior, scoring, routing, map rendering, or UI behavior.

## Live Baseline

Task 034C started after the required gate was verified:

```text
PR #91: closed / merged
PR #91 merge commit: 566de7de1eca2dc0e4771eca8e158772569d3d3d
Issue #90: closed / completed
Issue #92: open
base main SHA: 566de7de1eca2dc0e4771eca8e158772569d3d3d
open PRs before Task 034C: none
```

Task 034B and EXP-20260714-048 are present on `main`.

## Current Implemented Surfaces

### Pure formatter

`src/uav_rf_terrain/preview_appendix_table.py` implements:

```python
def format_fresnel_diagnostics_appendix_table(
    preview: Mapping[str, object],
    *,
    max_rows: int | None = None,
) -> str:
    ...
```

The function returns a deterministic 14-column Markdown table without a trailing newline. It performs no file I/O and preserves the approved diagnostic status, precision, ordering, MGRS, and omission contracts.

### Default appendix table

`format_preview_appendix_table(...)` remains the fixed 11-column default table. It continues to ignore diagnostic extras and does not perform diagnostic-aware validation.

### Report

`format_preview_report(preview, *, include_table=True)` currently contains:

```text
## Fresnel Diagnostics
## Appendix Table
```

The first section is a candidate-by-candidate narrative. `## Appendix Table` remains the existing 11-column table. The 14-column diagnostic table is not automatically inserted.

### CLI

The current CLI supports exactly one source:

```text
--synthetic
--input-json PATH
```

Current output selectors are:

```text
--json
--table
--report
--output-json PATH
--output-text PATH
--output-table PATH
--output-report PATH
```

The selectors are mutually exclusive. There is no diagnostic-table CLI or file-output option.

### Saved preview JSON

Saved preview JSON input is implemented. It is currently accepted only with table or report output. A diagnostic-table CLI mode may support saved JSON because the formatter already accepts the same preview dictionary contract.

## Alternatives Compared

| Alternative | Backward compatibility | Report impact | CLI impact | Traceability value | Decision |
|---|---|---|---|---|---|
| A. Keep Python API only | Maximum compatibility | None | None | Limited to Python callers | Rejected as the final delivery state |
| B. Always insert into every report | Changes all report snapshots and length | High | Indirectly changes report stdout/file | High but mandatory and duplicative | Rejected |
| C. Add explicit report formatter opt-in | Default can remain stable | Adds a second report schema | No direct CLI delivery unless additional work is added | High | Deferred to a separate reviewed task |
| D. Add CLI stdout mode | Default modes remain stable | None | Adds one explicit output selector | High | Included in selected staged design |
| E. Add CLI file-output option | Default modes remain stable | None | Adds one explicit output selector and reuses file policy | High | Included in selected staged design |
| F. Stage CLI stdout/file first; review report composition later | Preserves all defaults and limits implementation scope | None in first stage | Two explicit opt-in selectors | High with contained regression scope | Selected |

## Selected Delivery Strategy

Alternative F is selected.

Task 034D should connect the existing pure formatter to CLI stdout and explicit file output only. It should not change report composition.

The staged design separates two different user needs:

1. direct acquisition of the exact 14-column table for paper or developer review;
2. possible future composition of that wide table into a longer report.

The first need is already supported by a stable formatter and existing CLI/file helpers. The second changes report structure and snapshots and therefore remains a separate decision.

## Public Python API Contract

Task 034D does not change the formatter signature:

```python
def format_fresnel_diagnostics_appendix_table(
    preview: Mapping[str, object],
    *,
    max_rows: int | None = None,
) -> str:
    ...
```

No new report argument is approved by Task 034C.

Compatibility:

- existing Python callers remain valid;
- the function continues to return a string without a trailing newline;
- the 14-column schema, statuses, precision, order, omission sentence, error type, and no-file behavior remain unchanged.

## Exact CLI Options

Task 034D may add exactly these output selectors:

```text
--diagnostic-table
--output-diagnostic-table PATH
```

Meanings:

- `--diagnostic-table`: print the 14-column diagnostic appendix table to stdout;
- `--output-diagnostic-table PATH`: write the same table content to the explicit path.

These names align with the existing `--table` and `--output-table` surface while making the diagnostic schema explicit.

## Source Contract

Exactly one source remains required:

```text
--synthetic
--input-json PATH
```

Both sources are allowed with both diagnostic-table selectors.

`--input-json` without an allowed table/report/diagnostic-table output remains a parser error. Task 034D should extend the existing allowed saved-input output set to include:

```text
--diagnostic-table
--output-diagnostic-table PATH
```

It should not authorize `--input-json --json`, `--input-json --output-json`, or `--input-json --output-text`.

## Output Selector Contract

All output selectors belong to one explicit mutual-exclusion contract:

```text
--json
--table
--report
--diagnostic-table
--output-json PATH
--output-text PATH
--output-table PATH
--output-report PATH
--output-diagnostic-table PATH
```

At most one may be selected.

No output precedence is inferred. Any pair of selectors is a parser error with status 2 and no output artifact.

Examples of invalid combinations include:

```text
--table --diagnostic-table
--report --diagnostic-table
--diagnostic-table --output-diagnostic-table x.md
--output-table a.md --output-diagnostic-table b.md
--json --diagnostic-table
```

The existing parser message may remain:

```text
output selectors cannot be used together
```

## `--max-records` Contract

Task 034D should reuse the existing option:

```text
--max-records N
```

No new `--max-rows` or diagnostic-specific limit option is added.

For both diagnostic-table selectors:

```text
formatter max_rows = args.max_records
```

The same positive-integer validation applies. `None` means all candidates.

The existing report restriction remains unchanged:

```text
--max-records cannot be used with report output
```

Existing JSON behavior also remains unchanged: `--max-records` does not truncate JSON output.

## Stdout Contract

For `--diagnostic-table`:

1. build or load the preview;
2. call `format_fresnel_diagnostics_appendix_table(...)` exactly once;
3. print the returned table with exactly one trailing newline;
4. emit nothing to stderr on success;
5. create no file.

The formatter returns no trailing newline, so the CLI should use behavior equivalent to:

```python
print(diagnostic_table_text)
```

## File-Output Contract

For `--output-diagnostic-table PATH`:

1. build or load and validate the preview;
2. format the complete diagnostic table before opening or replacing the target;
3. reuse the existing `_write_text_output(...)` helper;
4. write UTF-8;
5. normalize to exactly one trailing newline;
6. do not create parent directories;
7. reject a directory path;
8. reject an existing target unless `--force` is present;
9. on success print exactly the existing confirmation pattern:

```text
preview saved: <PATH>
```

For the same source and `--max-records`, file content must be byte-for-byte identical to diagnostic-table stdout.

The existing helper does not claim crash-safe atomic replacement. The required no-partial-artifact guarantee applies to deterministic pre-write failures: input, diagnostic, parser, and path-validation errors must occur before target content is changed.

## Error and Exit Contract

### Parser and argument errors

Conditions:

```text
missing or multiple sources
multiple output selectors
invalid --max-records
bare --input-json or disallowed saved-input output
```

Contract:

```text
status: 2
stdout: empty
stderr: argparse error
artifact: none
```

### Input JSON errors

Contract remains:

```text
status: 1
stderr prefix: preview input error:
stdout: empty
artifact: none
```

### Diagnostic formatter errors

`PreviewAppendixTableError` from the diagnostic formatter should map to:

```text
status: 1
stderr prefix: preview diagnostic table error:
stdout: empty
artifact: absent or preserved
```

Invalid states include partial keys, mixed nulls, bool values, NaN, and infinity. A target must not be created, truncated, or overwritten when formatting fails, including when `--force` is present.

### File-output errors

Contract remains:

```text
status: 3
stderr prefix: output error:
stdout: empty
```

Examples:

```text
missing parent directory
output path is a directory
existing file without --force
write failure
```

Predictable path validation occurs before `write_text(...)`. Existing target content must be preserved for existing-file, directory, missing-parent, and pre-write formatter failures.

## Saved JSON State Compatibility

Diagnostic-table delivery supports the existing valid states:

```text
legacy/unavailable
eligible
no-eligible-obstacle
```

The exact 14-column formatter contract remains:

- legacy diagnostic cells: `unavailable`;
- no-eligible detail cells: `not-applicable`;
- eligible numeric precision unchanged;
- candidate order unchanged;
- internal coordinates and sample index not exposed.

Invalid saved records return status 1 through the diagnostic formatter error boundary.

## Report Relationship

Task 034D does not change:

```text
format_preview_report(...)
--report
--output-report
## Fresnel Diagnostics
## Appendix Table
```

The narrative diagnostic section and existing 11-column table remain exactly as currently implemented.

A future report opt-in may be considered only in a separate reviewed task. Task 034C does not approve a parameter name, heading, or automatic insertion point for that future change.

## Default Output Invariants

Task 034D must preserve exact regression behavior for:

```text
--synthetic default plain text
--json
--table
--report
--output-json
--output-text
--output-table
--output-report
```

It also preserves:

```text
preview JSON schema
plain-text preview content
11-column default table
14-column diagnostic table
report content and section order
existing file policy
existing status codes
```

## Scoring and Product Invariants

No delivery option changes:

```text
dsm_fresnel_score == average_fresnel_score
shielding_stability_score = dsm_los_score * 0.40 + dsm_fresnel_score * 0.60
overall_score = shielding_stability_score * 0.80 + distance_score * 0.20
strict LOS cap
color thresholds
candidate order or ranking
route cost
waypoint cost
map rendering or UI
```

Diagnostics remain offline terrain/surface support proxies. They are not a full link budget, RF field validation, RSSI, SINR, packet-loss, communication-success, reconnaissance-success, or flight-feasibility prediction.

## Task 034D Candidate Scope

Expected source change:

```text
src/uav_rf_terrain/preview_cli.py
```

Preferred focused test file:

```text
tests/test_diagnostic_appendix_cli_output.py
```

Existing CLI test files may receive narrowly scoped regression additions if needed:

```text
tests/test_preview_cli.py
tests/test_preview_table_cli_output.py
tests/test_preview_report_cli_output.py
```

Task 034D should not modify:

```text
src/uav_rf_terrain/preview_appendix_table.py
src/uav_rf_terrain/preview_report.py
src/uav_rf_terrain/candidate_display_preview.py
scoring, routing, waypoint, map, or UI modules
```

unless a concrete blocker is demonstrated and reviewed before expanding scope.

## Task 034D Test Matrix

```text
existing default CLI exact regression
existing JSON/table/report mode regression
--diagnostic-table synthetic stdout
--output-diagnostic-table synthetic file
saved JSON stdout
saved JSON file
stdout/file byte equality
UTF-8 and exactly one trailing newline
all output-selector conflicts
source-count validation
bare saved-input rejection
--max-records propagation and omission wording
legacy state
eligible state
no-eligible state
partial/mixed/bool/non-finite rejection
status 1 diagnostic errors
status 2 parser errors
status 3 file errors
missing parent and directory path
existing target preserved without --force
formatter failure preserves target even with --force
successful --force overwrite
no file creation for stdout
no internal coordinates or sample index
report snapshot unchanged
preview JSON and plain text unchanged
score/rank/route/waypoint/UI invariance
```

## Public Repository Sensitivity Check

This contract contains repository-relative paths and public interface decisions only. It adds no generated output, GIS/DEM/DSM data, `METADATA_MAP` content, credential, private local path, external-device command, autopilot command, or flight-control content.
