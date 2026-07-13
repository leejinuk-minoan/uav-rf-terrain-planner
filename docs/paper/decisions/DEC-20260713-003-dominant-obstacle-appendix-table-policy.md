# DEC-20260713-003 - Dominant Obstacle Appendix-Table Policy

## Decision

Provide dominant-obstacle diagnostics through a separate opt-in pure Markdown formatter in a future Task 034B implementation.

The existing default appendix table remains byte-contract compatible and does not gain diagnostic columns.

## Context

Task 033B exposes ten approved diagnostic fields in preview JSON, plain text, and report output. The default appendix table intentionally ignores those extras and retains a compact fixed-column contract.

Task 034A evaluates whether structured row-wise appendix output adds enough paper and review value to justify a separate output contract without destabilizing the default table.

## Alternatives

### A. Separate diagnostic appendix formatter

- preserves the default table exactly;
- makes caller intent explicit;
- isolates the wide diagnostic schema;
- reuses existing preview and diagnostic validation;
- supports saved preview dictionaries without schema migration.

### B. Opt-in mode on the existing formatter

- can preserve the default branch;
- gives one function two distinct header schemas;
- increases signature branching, snapshot ambiguity, and regression scope.

### C. Direct expansion of the default table

- changes every existing header and downstream table snapshot;
- makes the normal appendix excessively wide;
- breaks the strongest compatibility expectation.

### D. No diagnostic appendix output

- avoids implementation work;
- leaves the report as the only detailed human-readable surface;
- loses deterministic row-wise comparison and paper traceability value.

## Selected Design

Alternative A is selected.

Proposed API:

```python
def format_fresnel_diagnostics_appendix_table(
    preview: Mapping[str, object],
    *,
    max_rows: int | None = None,
) -> str:
    ...
```

The formatter belongs in `src/uav_rf_terrain/preview_appendix_table.py`, returns a string, performs no file I/O, and raises the existing `PreviewAppendixTableError` boundary.

## Rationale

A separate formatter provides structured diagnostic evidence without changing the compact default appendix. It makes the wide schema intentional, keeps legacy callers stable, and permits focused tests around diagnostic states.

The report already supplies a narrative diagnostic section. The new table therefore serves a different purpose: deterministic candidate-by-candidate comparison and paper appendix traceability.

## Compatibility Boundary

`format_preview_appendix_table(...)` remains unchanged in:

```text
signature
columns
column order
cell formatting
input order
row numbering
max_rows validation
omission wording
input immutability
file-persistence behavior
handling of diagnostic extras
```

The default formatter continues to ignore diagnostic extras and does not begin validating them.

## Output Schema

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

All ten approved diagnostic fields are included. `dominant_obstacle_sample_index` remains internal.

## Validation Behavior

Exact valid status strings:

```text
unavailable
eligible
no-eligible-obstacle
```

Representation:

- legacy record: status `unavailable`; ten value cells `unavailable`;
- eligible record: status `eligible`; ten finite numeric cells;
- no-eligible record: status `no-eligible-obstacle`; average numeric; remaining nine cells `not-applicable`.

Partial keys, mixed nulls, boolean numeric values, NaN, or infinity raise `PreviewAppendixTableError`. Invalid states produce no output row.

Validation should reuse `DIAGNOSTIC_FIELD_ORDER` and `validate_flat_fresnel_diagnostics(...)` rather than duplicate state logic.

## Precision

- scores: one decimal place;
- distance/elevation/clearance/Fresnel radius: one decimal place;
- clearance ratio: three decimal places;
- `nu`: three decimal places;
- diffraction loss: one decimal place.

Units remain encoded in field-name suffixes; cells contain numeric text only. Stored, JSON, and scoring values are not rounded or altered.

## Ordering and Row Limit

The new formatter preserves candidate input order, uses one-based row numbering, accepts the same `max_rows` contract, and uses the exact omission sentence:

```text
... N additional row(s) omitted.
```

The default and diagnostic formatters represent the same first-N subset when called with the same preview and `max_rows`.

## Coordinate Boundary

The only user-facing coordinate is:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
```

Internal projected coordinates, raster indices, WGS84 conversion fields, and `dominant_obstacle_sample_index` remain excluded.

`dominant_obstacle_distance_from_start_m` is a path-relative scalar, not an independent map coordinate.

## Scoring Boundary

The decision does not change:

```text
dsm_fresnel_score == average_fresnel_score
shielding_stability_score = dsm_los_score * 0.40 + dsm_fresnel_score * 0.60
overall_score = shielding_stability_score * 0.80 + distance_score * 0.20
strict LOS cap
color thresholds
candidate ranking
route cost
waypoint cost
```

## Paper Boundary

The diagnostic table is suitable as a detailed appendix or developer-review artifact. It is not evidence of measured RF performance or algorithmic field validity.

No generated table artifact is committed by Task 034A.

## Product and Deployment Boundary

Task 034B does not add CLI options, file-output commands, report composition, map rendering, UI widgets, mobile packaging, external-device output, or flight-control behavior.

A future CLI/file-output or report-composition surface requires a separate reviewed boundary.

## Follow-Up Implementation Task

Task 034B may implement the new pure formatter and focused regression tests in:

```text
src/uav_rf_terrain/preview_appendix_table.py
tests/test_preview_appendix_table.py
tests/test_dominant_obstacle_preview_integration.py
```

Other runtime modules remain unchanged unless a concrete blocker is demonstrated and reported before scope expansion.

## Public Repository Sensitivity Check

This decision contains repository contracts only. It adds no private path, credential, GIS data, DEM/DSM raster, `METADATA_MAP` content, generated output artifact, operational command, autopilot command, or device-control content.
