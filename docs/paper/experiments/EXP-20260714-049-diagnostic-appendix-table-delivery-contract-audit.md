# EXP-20260714-049 - Diagnostic Appendix Table Delivery Contract Audit

## Audit Purpose

Audit the implemented diagnostic appendix formatter, current report contract, current CLI/file-output contract, saved JSON input surface, and related tests to define a backward-compatible delivery boundary.

This record is a code/document contract audit. It is not a runtime experiment, local test execution record, RF validation, or field test.

## Baseline Evidence

```text
PR #91: merged
merge commit: 566de7de1eca2dc0e4771eca8e158772569d3d3d
Issue #90: closed / completed
Issue #92: open
base main SHA: 566de7de1eca2dc0e4771eca8e158772569d3d3d
```

Task 034B implementation and EXP-048 were present on the audited `main` tree.

## Files Audited

Documentation included:

```text
AGENTS.md
CLAUDE.md
README.md
docs/master-plan.md
docs/research/research-index.md
docs/architecture/dominant-obstacle-appendix-table-output-boundary.md
docs/architecture/dominant-obstacle-preview-report-output-boundary.md
docs/handoff/task-034b-dominant-obstacle-diagnostic-appendix-table-implementation.md
docs/paper/decisions/DEC-20260713-003-dominant-obstacle-appendix-table-policy.md
docs/paper/experiments/EXP-20260714-048-dominant-obstacle-diagnostic-appendix-table-implementation.md
docs/paper/decisions/README.md
docs/paper/experiments/README.md
.github/workflows/ci.yml
```

Runtime and tests were read but not modified:

```text
src/uav_rf_terrain/preview_appendix_table.py
src/uav_rf_terrain/preview_report.py
src/uav_rf_terrain/preview_cli.py
src/uav_rf_terrain/candidate_display_preview.py
tests/test_preview_appendix_table.py
tests/test_preview_report.py
tests/test_preview_cli.py
tests/test_preview_table_cli_output.py
tests/test_preview_report_cli_output.py
```

## Current-State Findings

### Formatter

The pure 14-column formatter is implemented and stable. It returns a Markdown string without file I/O and supports legacy, eligible, and no-eligible states. Invalid diagnostic states raise `PreviewAppendixTableError`.

### Default table

The default 11-column formatter remains independent and continues to ignore diagnostic extras.

### Report

The report has a narrative `## Fresnel Diagnostics` section and the existing default `## Appendix Table`. It does not compose the 14-column diagnostic table.

### CLI

The CLI has one-source validation, mutually exclusive outputs, `--max-records`, saved JSON input, UTF-8 output helpers, overwrite protection, and status codes 0/1/2/3. No diagnostic-table output selector exists.

### Saved JSON

Saved JSON input is real and implemented. It currently supports table/report output. The same preview dictionary can be passed to the diagnostic formatter, including legacy, eligible, and no-eligible records.

## Alternatives Audited

```text
A. Python API-only
B. always add to report
C. report opt-in
D. CLI stdout
E. CLI file output
F. staged CLI stdout/file then later report review
```

Alternative F was selected.

## Selected Contract

Task 034D should add:

```text
--diagnostic-table
--output-diagnostic-table PATH
```

Both selectors are opt-in and mutually exclusive with every existing output selector.

Both support:

```text
--synthetic
--input-json PATH
```

`--max-records` is reused and passed as formatter `max_rows`.

Task 034D should not change report composition.

## Stdout and File Findings

The current CLI already establishes a reusable symmetry:

- formatter text is printed with one trailing newline;
- `_write_text_output(...)` writes UTF-8 with one trailing newline;
- file content matches stdout for existing table/report surfaces;
- parent directories are not created;
- existing targets require `--force`;
- file errors return status 3.

The diagnostic delivery contract reuses this behavior.

## Error Contract Findings

Recommended mapping:

```text
invalid arguments: 2
input/diagnostic error: 1
file/path/write error: 3
success: 0
```

Diagnostic errors use the distinct stderr prefix:

```text
preview diagnostic table error:
```

Formatting must precede file writing so invalid diagnostics cannot overwrite an existing target, including under `--force`.

## Backward-Compatibility Result

The selected contract does not change:

```text
default plain text
JSON stdout/file
default table stdout/file
report stdout/file
preview JSON schema
11-column default table
14-column diagnostic schema
report section order
scoring, color, rank
route or waypoint cost
map or UI behavior
```

## Task 034D Test Matrix

```text
existing default CLI exact regression
existing JSON/table/report regression
synthetic diagnostic stdout
synthetic diagnostic file
saved JSON diagnostic stdout/file
stdout/file byte equality
UTF-8 and one trailing newline
all output-selector conflicts
source validation
max-records propagation
legacy/eligible/no-eligible
invalid diagnostics
status 1/2/3 mapping
path and overwrite policy
pre-write failure preserves target
no stdout file creation
MGRS and internal-coordinate boundary
report snapshot unchanged
scoring/routing/UI invariance
```

## Local and CI Evidence Boundary

No local command was executed for Task 034C. Task 034B local results in EXP-048 remain separate historical evidence.

GitHub Actions evidence for the Task 034C Draft PR is recorded only after the PR runs on its actual head.

## Interpretation

The selected CLI delivery makes the existing deterministic table reproducible from both synthetic and saved-preview inputs without destabilizing the report contract. It improves paper and developer traceability while retaining explicit opt-in semantics.

## Limitations

This audit does not generate the new CLI output, validate implementation behavior, measure RF propagation, reconstruct a full link budget, or predict communication, reconnaissance, or flight outcomes.

## Figure and Table Candidacy

The 14-column output is a candidate paper appendix artifact after Task 034D implements and verifies the delivery surface. This audit alone is not generated-output evidence.

## Public Repository Sensitivity Check

The audit uses repository contracts and synthetic-test documentation only. It adds no generated table, DEM/DSM/GIS data, `METADATA_MAP` content, credential, private path, operational command, autopilot command, device-control command, or flight-control content.
