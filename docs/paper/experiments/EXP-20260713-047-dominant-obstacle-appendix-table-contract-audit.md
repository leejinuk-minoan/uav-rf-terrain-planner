# EXP-20260713-047 - Dominant Obstacle Appendix-Table Contract Audit

## Audit Purpose

Audit the current appendix-table formatter, diagnostic preview/report contract, focused tests, and durable documentation. Select and document one backward-compatible appendix-table output contract for a future Task 034B implementation.

This is a code/document contract audit.

This is not runtime execution.

This is not local test evidence.

This is not RF or field validation.

## Start Gate Evidence

```text
PR #87: merged
PR #87 merge commit: 740d3a5ee5e8edec2c3de3cff9e83265ee740dc5
Issue #86: closed / completed
Issue #88: open
base main SHA: 740d3a5ee5e8edec2c3de3cff9e83265ee740dc5
```

## Files Inspected

Runtime and test contracts inspected without modification:

```text
src/uav_rf_terrain/preview_appendix_table.py
src/uav_rf_terrain/candidate_display_preview.py
src/uav_rf_terrain/preview_report.py
src/uav_rf_terrain/fresnel_diagnostics.py
tests/test_preview_appendix_table.py
tests/test_dominant_obstacle_preview_integration.py
```

Durable documents inspected included:

```text
AGENTS.md
CLAUDE.md
README.md
docs/master-plan.md
docs/research/research-index.md
docs/architecture/dominant-obstacle-preview-report-output-boundary.md
docs/architecture/fresnel-dominant-obstacle-integration.md
docs/handoff/task-033b-dominant-obstacle-preview-report-integration.md
docs/handoff/task-033c-post-merge-documentation-reconciliation.md
docs/paper/decisions/DEC-20260713-002-dominant-obstacle-diagnostic-output-policy.md
docs/paper/experiments/EXP-20260713-045-dominant-obstacle-preview-report-integration.md
docs/paper/experiments/EXP-20260713-046-task-033b-post-merge-documentation-audit.md
docs/paper/decisions/README.md
docs/paper/experiments/README.md
.github/workflows/ci.yml
```

## Current-Code Findings

The default appendix formatter has a fixed 11-column Markdown contract and ignores diagnostic extra keys. It preserves order, supports positive integer `max_rows`, reports omitted rows, rejects empty input and internal coordinates, does not mutate input, and creates no files.

Diagnostic state validation already exists in `fresnel_diagnostics.py`:

```text
legacy
eligible
no_eligible
```

Partial keys, mixed nulls, booleans, NaN, and infinity are rejected in diagnostic-aware paths.

The report already renders a detailed `## Fresnel Diagnostics` narrative section. Its embedded appendix remains the compact default table.

## Alternative Matrix

| Alternative | Backward compatibility | Intent clarity | Paper traceability | Complexity | Audit conclusion |
|---|---|---|---|---|---|
| A. Separate diagnostic formatter | Strongest; default untouched | Explicit | High; row-wise detailed schema | Focused new formatter/tests | Selected |
| B. Existing formatter opt-in flag | Default can remain stable | Mode-dependent | High | One function owns two schemas | Rejected |
| C. Direct default expansion | Breaks header/snapshots | Simple | High | Broad downstream regression | Rejected |
| D. No appendix diagnostic table | No change | Clear | Limited to narrative report | No implementation | Rejected |

## Selected Contract

Proposed pure API:

```python
format_fresnel_diagnostics_appendix_table(
    preview,
    *,
    max_rows=None,
)
```

The existing `format_preview_appendix_table(...)` remains unchanged.

Exact columns:

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

All ten approved values remain in one detailed table. `dominant_obstacle_sample_index` remains excluded.

## State and Null Contract

```text
legacy/un-enriched
→ diagnostic_status = unavailable
→ ten value cells = unavailable

enriched with eligible obstacle
→ diagnostic_status = eligible
→ ten finite formatted numeric cells

enriched with no eligible obstacle
→ diagnostic_status = no-eligible-obstacle
→ average numeric
→ remaining nine cells = not-applicable
```

Invalid partial, mixed-null, boolean, NaN, or infinity states raise `PreviewAppendixTableError` and produce no row.

## Precision Contract

```text
scores: 1 decimal
distance/elevation/clearance/radius: 1 decimal
clearance ratio: 3 decimals
nu: 3 decimals
diffraction loss: 1 decimal
```

Units are encoded in column names. Cells do not append unit strings. Stored and JSON values are not changed.

## Ordering and Row-Limit Contract

- input candidate order preserved;
- one-based visible `row_no`;
- `max_rows=None` means all rows;
- positive non-boolean integer required otherwise;
- omission text exactly `... N additional row(s) omitted.`;
- empty input rejected;
- input not mutated;
- no file created;
- same preview and same limit produce the same first-N subset in default and diagnostic tables.

## Coordinate and Sensitivity Audit

The only user-facing coordinate remains `candidate_cell_mgrs` under MGRS policy.

Internal x/y, row/col, raster indices, EPSG/internal projected coordinates, WGS84 conversion fields, and `dominant_obstacle_sample_index` remain excluded.

No credential, private path, generated artifact, GIS data, DEM/DSM raster, QGIS project, or `METADATA_MAP` content is introduced.

## Preserved Invariants

```text
dsm_fresnel_score == average_fresnel_score
shielding_stability_score = dsm_los_score * 0.40 + dsm_fresnel_score * 0.60
overall_score = shielding_stability_score * 0.80 + distance_score * 0.20
strict LOS cap
color thresholds
candidate order/ranking
route cost
waypoint cost
```

Report behavior, CLI options, map rendering, and UI behavior remain unchanged by Task 034A.

## Task 034B Test Matrix

```text
default table exact regression
legacy diagnostic state
eligible diagnostic state
no-eligible diagnostic state
partial-key rejection
mixed-null rejection
bool rejection
NaN/infinity rejection
exact columns/order
precision
unavailable/not-applicable strings
candidate order
max_rows validation and omission wording
input immutability
internal-coordinate rejection
sample-index non-exposure
no file creation
saved JSON compatibility
report remains unchanged
CLI remains unchanged
score/color/rank/route/waypoint invariance
```

## Limitations

The audit does not execute the proposed formatter, generate a table artifact, rerun local tests, or validate radio propagation against measurements.

The diagnostics remain offline terrain/surface support proxies. They are not a full link budget or predictions of RSSI, SINR, packet loss, communication success, reconnaissance success, or flight feasibility.

## Paper Traceability Value

The selected separate table contract supports deterministic candidate-by-candidate appendix comparison while keeping the compact default table stable. It separates narrative interpretation in the report from detailed row-wise evidence in an optional appendix artifact.
