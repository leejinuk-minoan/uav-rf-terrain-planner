# EXP-20260713-046 - Task 033B Post-Merge Documentation Audit

## Audit Purpose

Audit the post-merge repository and durable documentation state after Task 033B was merged through PR #85, then reconcile stale pre-merge wording.

This record is a code/document state audit. It is not a runtime experiment, RF experiment, algorithm validation, local command execution record, or field test.

## Evidence Sources

The audit used live GitHub metadata and current `main` documentation:

```text
PR #85 metadata and discussion
Issue #84
Issue #86
main commit history
CI #770 summary
CI #772 summary and job steps
current changed-file and file-presence checks
current repository documents
```

## Files Inspected

Mandatory current-state documents included:

```text
README.md
AGENTS.md
CLAUDE.md
docs/master-plan.md
docs/research/research-index.md
docs/architecture/fresnel-dominant-obstacle-integration.md
docs/architecture/dominant-obstacle-preview-report-output-boundary.md
docs/handoff/task-033b-dominant-obstacle-preview-report-integration.md
docs/paper/experiments/EXP-20260713-045-dominant-obstacle-preview-report-integration.md
docs/paper/experiments/README.md
.github/workflows/ci.yml
```

README was already factually current and was not modified.

## Stale-State Findings

Five durable documents still contained current-state wording equivalent to:

```text
Draft PR #85
Task 033B unmerged
not yet on main
final amended head CI still requires verification
merge status requires future review
```

These statements were accurate before the final merge but became stale after 2026-07-13T13:04:38Z.

## Reconciliation Performed

The audit updates the five affected documents to record:

```text
PR #85: merged
Issue #84: completed
Task 033B: complete on main
final PR head: db0b555f72b802c0ecc53cac3276e47815ae121c
merge commit: 33f93f68cd22efde9a3d7b8ae1aae0713681860c
```

The implementation path is preserved as:

```text
FresnelAnalysis
→ CandidateFresnelDiagnostics
→ SyntheticCandidateRecord
→ CandidateCellMapFeature
→ CandidateDisplayRecord
→ preview dictionary
→ plain text / JSON / report
```

The documentation also preserves legacy preview compatibility, ten-field eligible output, finite average plus nine nulls for no-eligible records, diagnostic-aware invalid-state rejection, unchanged appendix-table columns, and unchanged score/order boundaries.

## PR #85 Merge Evidence

```text
state: closed
merged: true
final head: db0b555f72b802c0ecc53cac3276e47815ae121c
merge commit: 33f93f68cd22efde9a3d7b8ae1aae0713681860c
merged at: 2026-07-13T13:04:38Z
Issue #84: closed / completed
```

## CI Evidence

Initial implementation reviewed head:

```text
CI #770
head: 31ad2abcb27df940048dc0e7678888ff5e9c11a5
status: completed
conclusion: success
```

Final PR head:

```text
CI #772
head: db0b555f72b802c0ecc53cac3276e47815ae121c
status: completed
conclusion: success
install: success
syntax check: success
pytest: success
Ruff: success
mypy: success
```

CI #770 and CI #772 are distinct observations for different commit heads.

## Protected-Path Audit

Task 033C is documentation-only. The intended changed-file set excludes:

```text
src/
tests/
.github/workflows/
pyproject.toml
lock files
```

The standard CI workflow remains unchanged. No new runner, matrix, cache, artifact, package upload, release asset, Git LFS use, or terrain-data download is introduced.

## Cleanup-History and Placeholder Audit

The audit observed the post-merge cleanup commits:

```text
08fbab9cd7f0eb187fd90e35a298dcbd4e20d260
04390aab1312bf4bc4c8a9a9e5b3008a4eab8403
```

The current `main` tree has no root `placeholder` file. The cleanup commits and repository history are not rewritten.

## Public-Repository Sensitivity Audit

No generated JSON, report, table, image, PDF, CSV, archive, DEM/DSM, GIS data, QGIS project, `METADATA_MAP` content, credential, private local path, or internal user-facing coordinate is added.

The record contains only repository-relative paths and public GitHub state evidence.

## Preserved Analysis Boundaries

Task 033B diagnostics remain support information only. They do not alter:

```text
dsm_fresnel_score meaning
shielding_stability_score
overall_score
strict LOS cap
color classification
candidate ordering or ranking
route cost
waypoint cost
appendix-table columns
CLI option surface
```

Map features carry typed diagnostic data, but Task 033B did not add map rendering or UI visualization.

## Limitations

This audit establishes documentation consistency with observed repository state. It does not independently rerun local commands, reproduce generated preview/report output, validate RF propagation against measurements, reconstruct a full link budget, or predict communication, reconnaissance, or flight outcomes.

## Paper Traceability Value

EXP-046 distinguishes three evidence layers for later paper drafting:

1. Local Execution Agent integration and regression evidence recorded in EXP-045;
2. GitHub Actions evidence for the initial and final PR heads;
3. post-merge repository/document-state audit confirming that durable records match the merged implementation.

This separation prevents pre-merge wording or CI evidence from being misrepresented as final merged-state evidence.
