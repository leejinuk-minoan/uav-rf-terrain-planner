# DEC-20260714-004 - Diagnostic Appendix Table Delivery Policy

## Decision

Deliver the implemented 14-column dominant-obstacle diagnostic appendix table through explicit CLI stdout and file-output selectors in Task 034D, while leaving report composition unchanged.

Selected strategy:

```text
staged expansion
Task 034D: CLI stdout and explicit file output
future reviewed task: optional report composition, if still required
```

## Context

Task 034B implements:

```python
format_fresnel_diagnostics_appendix_table(
    preview,
    *,
    max_rows=None,
)
```

The formatter is currently available only through Python. The default 11-column table, JSON, plain-text preview, report, and CLI options remain unchanged.

A delivery decision is required because adding the table to every report would change a stable document contract, while retaining Python-only access limits paper and developer traceability for non-Python users.

## Alternatives

### A. Python API-only

- preserves all public CLI/report behavior;
- requires direct Python use;
- provides no explicit saved-JSON command-line delivery;
- does not fully satisfy paper/developer artifact workflows.

### B. Always insert into reports

- makes the table universally visible;
- changes every default report and snapshot;
- duplicates the existing narrative `## Fresnel Diagnostics` section;
- substantially increases report width and length.

### C. Explicit report opt-in

- can preserve the default report;
- introduces a second report schema and composition test surface;
- requires decisions on heading, position, duplication, and CLI forwarding;
- is useful but not necessary for direct table delivery.

### D. CLI stdout only

- provides simple terminal delivery;
- preserves defaults;
- does not provide a direct reviewable file without shell redirection.

### E. CLI file output only

- provides an explicit artifact path;
- preserves defaults;
- lacks a quick stdout inspection mode and breaks symmetry with the existing table surface.

### F. Staged CLI stdout/file, later report review

- preserves all current default output and report behavior;
- reuses the existing CLI selector and file policies;
- provides both quick inspection and explicit UTF-8 file delivery;
- isolates report composition as a separate decision.

## Selected Design

Alternative F is selected.

Task 034D should add two output selectors only:

```text
--diagnostic-table
--output-diagnostic-table PATH
```

No report API, heading, section, or snapshot change is approved in Task 034D.

## Backward Compatibility

The following remain unchanged:

```text
format_preview_appendix_table(...) 11-column output
format_fresnel_diagnostics_appendix_table(...) 14-column output
preview JSON schema
plain-text preview
format_preview_report(...) output
--json / --table / --report
--output-json / --output-text / --output-table / --output-report
default synthetic plain-text mode
```

The new selectors are opt-in and are added to the existing mutual-exclusion rule.

## Public API Contract

The formatter signature remains:

```python
def format_fresnel_diagnostics_appendix_table(
    preview: Mapping[str, object],
    *,
    max_rows: int | None = None,
) -> str:
    ...
```

Return type: `str`.

The returned formatter string has no trailing newline. Task 034D must not change this contract.

## CLI Contract

### Exact options

```text
--diagnostic-table
--output-diagnostic-table PATH
```

### Sources

Exactly one remains required:

```text
--synthetic
--input-json PATH
```

Both sources support both new selectors.

### Mutual exclusion

The new selectors join one output-selector set with all existing selectors. At most one may be used.

No implicit priority is defined. Conflicts are parser errors.

### Saved input

`--input-json` is allowed with:

```text
--table
--output-table PATH
--report
--output-report PATH
--diagnostic-table
--output-diagnostic-table PATH
```

Existing prohibitions for saved-input JSON/text echo modes remain unchanged.

## Row-Limit Contract

Reuse:

```text
--max-records N
```

For diagnostic table output:

```text
max_rows = args.max_records
```

No new limit option is approved.

The current report prohibition remains. Existing JSON behavior remains unchanged.

## Stdout and File Contract

Both outputs use the same formatter and the same source preview.

For identical source and limit:

```text
stdout content == file content
```

Both contain exactly one trailing newline at the delivery surface.

File output:

- UTF-8;
- reuses `_write_text_output(...)`;
- does not create parent directories;
- rejects directory paths;
- rejects existing targets without `--force`;
- permits overwrite with `--force`;
- prints `preview saved: <PATH>` on success.

Input and diagnostic validation occur before target writing. Deterministic pre-write failures must not create, truncate, or replace the target.

## Option Combination Contract

Examples rejected with status 2:

```text
--table --diagnostic-table
--report --diagnostic-table
--diagnostic-table --output-diagnostic-table x.md
--output-table a.md --output-diagnostic-table b.md
--json --diagnostic-table
```

Bare `--input-json PATH` remains invalid.

## Error and Exit Contract

```text
0 = success
1 = preview input, synthetic preview, or diagnostic formatter error
2 = parser or argument contract error
3 = output path or write error
```

Diagnostic formatter failure:

```text
stderr prefix: preview diagnostic table error:
stdout: empty
artifact: absent or existing content preserved
```

File failure retains the existing `output error:` prefix.

Task 034D should format before writing, including before a forced overwrite.

## Report Relationship

The current report remains unchanged:

```text
## Fresnel Diagnostics
## Appendix Table
```

The first is narrative diagnostic content. The second is the existing default table.

Task 034C does not approve automatic insertion or a report opt-in parameter. A future report decision must separately address document duplication, heading, position, length, and snapshot compatibility.

## Paper Boundary

The diagnostic table is suitable for appendix and developer-review traceability. CLI/file delivery makes the existing formatter easier to reproduce from synthetic or saved JSON input.

The output is not RF measurement evidence and does not establish field validity.

## Product and Deployment Boundary

Task 034D is a command-line delivery extension only. It does not add UI, map rendering, mobile packaging, external-device integration, autopilot behavior, or flight-control behavior.

## Analysis Invariants

No change is authorized to:

```text
dsm_fresnel_score == average_fresnel_score
shielding_stability_score = dsm_los_score * 0.40 + dsm_fresnel_score * 0.60
overall_score = shielding_stability_score * 0.80 + distance_score * 0.20
strict LOS cap
color thresholds
candidate order or ranking
route cost
waypoint cost
```

Diagnostics remain offline terrain/surface support proxies, not full-link-budget, RSSI, SINR, packet-loss, communication-success, reconnaissance-success, or flight-feasibility predictions.

## Task 034D Scope

Expected source file:

```text
src/uav_rf_terrain/preview_cli.py
```

Preferred focused test file:

```text
tests/test_diagnostic_appendix_cli_output.py
```

Narrow regression additions may be made to existing CLI tests. Formatter and report source files should remain unchanged unless a concrete blocker is reported and reviewed.

## Public Repository Sensitivity Check

This decision contains public interface contracts only. It adds no generated output, GIS/DEM/DSM data, `METADATA_MAP` content, credential, private path, operational command, device-control command, autopilot command, or flight-control content.
