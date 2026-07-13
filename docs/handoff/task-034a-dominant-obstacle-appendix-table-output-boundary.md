# Task 034A Dominant Obstacle Appendix-Table Output Boundary

## Purpose

Define a reviewed, backward-compatible contract for optional dominant-obstacle diagnostic appendix-table output without implementing runtime behavior.

## Live Baseline

Verified before branch creation:

```text
repository: leejinuk-minoan/uav-rf-terrain-planner
Issue #88: open
PR #87: closed / merged
PR #87 merge commit: 740d3a5ee5e8edec2c3de3cff9e83265ee740dc5
Issue #86: closed / completed
base main SHA: 740d3a5ee5e8edec2c3de3cff9e83265ee740dc5
open PRs before Task 034A: none
related open appendix-diagnostic issue: #88 only
```

## Branch and Draft PR

```text
branch: agent/task-034a-diagnostic-appendix-table-contract
Draft PR: pending creation after initial documentation commit
PR title: docs: define diagnostic appendix table boundary
```

The PR must remain Draft and include `Closes #88`.

## Audit Scope

Runtime and test files were inspected but not modified:

```text
src/uav_rf_terrain/preview_appendix_table.py
src/uav_rf_terrain/candidate_display_preview.py
src/uav_rf_terrain/preview_report.py
src/uav_rf_terrain/fresnel_diagnostics.py
tests/test_preview_appendix_table.py
tests/test_dominant_obstacle_preview_integration.py
```

The audit confirmed that the default appendix table remains a fixed 11-column contract and that diagnostic-aware validation already exists as a reusable pure helper.

## Selected Contract Summary

Recommendation: add a separate pure formatter in Task 034B.

```python
format_fresnel_diagnostics_appendix_table(
    preview,
    *,
    max_rows=None,
)
```

The default `format_preview_appendix_table(...)` remains byte-contract compatible and continues to ignore diagnostic extra keys.

Exact diagnostic table columns:

```text
row_no
candidate_id
candidate_cell_mgrs
diagnostic_status
average_fresnel_score
worst_obstacle_score
dominant_obstacle_distance_from_start_m
dominant_obstacle_dsm_msl
dominant_obstacle_los_msl
dominant_obstacle_clearance_m
dominant_obstacle_clearance_ratio
dominant_obstacle_fresnel_radius_m
dominant_obstacle_nu
dominant_obstacle_diffraction_loss_db
```

Exact statuses:

```text
unavailable
eligible
no-eligible-obstacle
```

Exact absent-value strings:

```text
legacy diagnostic value: unavailable
valid no-eligible obstacle detail: not-applicable
```

## Rejected Alternatives

- Existing formatter opt-in flag: rejected because one function would own two incompatible schemas and a larger regression surface.
- Direct default-table expansion: rejected because it breaks the header and downstream byte contract.
- No diagnostic table: rejected because the report narrative does not replace deterministic row-wise appendix comparison.

## Ordering and Precision

The new table preserves candidate order, uses one-based row numbers, applies the existing positive `max_rows` contract, and uses the exact omission sentence `... N additional row(s) omitted.`.

Formatting:

```text
scores: 1 decimal
distance/elevation/clearance/radius: 1 decimal
clearance ratio: 3 decimals
nu: 3 decimals
diffraction loss: 1 decimal
```

Units remain in field-name suffixes rather than cell values.

## Validation and Coordinates

Task 034B should reuse `validate_flat_fresnel_diagnostics(...)` and `DIAGNOSTIC_FIELD_ORDER`.

Partial keys, mixed nulls, boolean values, NaN, and infinity raise `PreviewAppendixTableError` in the diagnostic formatter.

The only user-facing coordinate remains `candidate_cell_mgrs` in MGRS. Internal coordinates and `dominant_obstacle_sample_index` remain excluded.

## Documents Changed

New:

```text
docs/architecture/dominant-obstacle-appendix-table-output-boundary.md
docs/handoff/task-034a-dominant-obstacle-appendix-table-output-boundary.md
docs/paper/decisions/DEC-20260713-003-dominant-obstacle-appendix-table-policy.md
docs/paper/experiments/EXP-20260713-047-dominant-obstacle-appendix-table-contract-audit.md
```

Updated:

```text
docs/paper/decisions/README.md
docs/paper/experiments/README.md
docs/architecture/dominant-obstacle-preview-report-output-boundary.md
docs/research/research-index.md
```

## Protected Paths

Task 034A does not modify:

```text
src/
tests/
.github/workflows/
pyproject.toml
lock files
```

It does not implement a formatter, CLI option, report section, scoring change, color change, ranking change, route/waypoint change, or map/UI behavior.

## CI Evidence

Initial Draft PR CI evidence will be added after the PR is created and the standard GitHub Actions workflow completes.

The Cloud Execution Agent does not claim local execution of compileall, pytest, Ruff, mypy, CLI, report generation, rasterio, GDAL, or QGIS.

## Limitations

This is a code/document contract audit only. It does not generate appendix output, validate RF propagation, reconstruct a full link budget, or predict communication, reconnaissance, or flight outcomes.

## Task 034B Implementation Handoff

Preferred narrow source scope:

```text
src/uav_rf_terrain/preview_appendix_table.py
```

Focused test scope:

```text
tests/test_preview_appendix_table.py
tests/test_dominant_obstacle_preview_integration.py
```

Task 034B should not modify report composition, CLI behavior, preview schema, scoring, color, ranking, route, waypoint, or UI unless a concrete blocker is first reported and reviewed.
