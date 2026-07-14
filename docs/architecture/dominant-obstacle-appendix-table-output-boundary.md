# Dominant Obstacle Diagnostic Appendix-Table Output Boundary

## Purpose

This document records the implemented contract for the optional 14-column dominant-obstacle diagnostic Markdown table and its relationship to the default appendix table.

The user-facing delivery decision is defined separately in:

```text
docs/architecture/diagnostic-appendix-table-delivery-boundary.md
```

## Current Implementation State

Task 034B is complete on `main` through PR #91.

```text
PR #91: merged
merge commit: 566de7de1eca2dc0e4771eca8e158772569d3d3d
Issue #90: closed / completed
```

Implemented API:

```python
def format_fresnel_diagnostics_appendix_table(
    preview: Mapping[str, object],
    *,
    max_rows: int | None = None,
) -> str:
    ...
```

Implementation location:

```text
src/uav_rf_terrain/preview_appendix_table.py
```

The formatter is a pure Python API. It returns Markdown text, creates no file, performs no coordinate conversion, and does not change scoring or candidate ordering.

## Default Appendix Table Compatibility

The existing default API remains:

```python
format_preview_appendix_table(
    preview,
    *,
    max_rows=None,
)
```

Its exact 11 columns remain:

```text
row_no
candidate_id
candidate_cell_mgrs
color_class
color_name
overall_score
shielding_stability_score
source_zone
source_sensitive
source_zone_reason
candidate_reason
```

The default formatter continues to preserve:

```text
signature
columns and column order
cell formatting
candidate input order
one-based row numbering
max_rows validation
... N additional row(s) omitted.
input immutability
no-file behavior
diagnostic extras ignored
```

Malformed diagnostic extras do not become a new failure mode for the default formatter.

## Diagnostic Table Columns

The separate diagnostic formatter uses exactly these 14 columns:

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

`dominant_obstacle_sample_index` remains internal and is not included.

## Diagnostic State Contract

Exact output status strings:

```text
unavailable
eligible
no-eligible-obstacle
```

### Legacy record

Condition:

```text
all ten diagnostic keys absent
```

Output:

```text
diagnostic_status = unavailable
all ten diagnostic value cells = unavailable
```

Absence is not interpreted as zero, a clear path, or no obstacle.

### Eligible record

Condition:

```text
all ten diagnostic keys present
all ten values finite numeric
```

Output:

```text
diagnostic_status = eligible
all ten cells formatted with approved precision
```

### No-eligible record

Condition:

```text
all ten diagnostic keys present
average_fresnel_score finite numeric
remaining nine values null
```

Output:

```text
diagnostic_status = no-eligible-obstacle
average_fresnel_score = formatted numeric
remaining nine cells = not-applicable
```

`not-applicable` is distinct from legacy `unavailable`.

### Invalid states

The formatter raises `PreviewAppendixTableError` and returns no table for:

```text
partial diagnostic field set
mixed numeric/null values
boolean numeric values
NaN
positive infinity
negative infinity
```

The implementation reuses `validate_flat_fresnel_diagnostics(...)` and translates its diagnostic error into the appendix-table error boundary.

## Precision Contract

| Field group | Markdown cell precision |
|---|---|
| average/worst score | one decimal place |
| distance, DSM MSL, LOS MSL, clearance, Fresnel radius | one decimal place |
| clearance ratio | three decimal places |
| `nu` | three decimal places |
| diffraction loss | one decimal place |

Units remain in the field names. Stored values, JSON values, analysis values, and scoring values are not rounded or changed.

## Ordering and Row Limit

The diagnostic formatter:

- preserves input candidate order;
- uses all records when `max_rows is None`;
- accepts only a positive non-boolean integer otherwise;
- displays the first `max_rows` records;
- numbers visible rows from 1;
- uses the exact omission sentence `... N additional row(s) omitted.`;
- rejects empty records;
- does not mutate input;
- creates no file.

For the same preview and limit, the default and diagnostic tables represent the same candidate subset in the same order.

## Coordinate Boundary

The only user-facing candidate coordinate remains:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
```

The output excludes:

```text
x_m
y_m
row
col
raster_row
raster_col
EPSG/internal projected coordinates
WGS84/internal conversion fields
dominant_obstacle_sample_index
```

`dominant_obstacle_distance_from_start_m` is a path-relative scalar, not an independent map coordinate.

## Current Report Relationship

The report contains:

```text
## Fresnel Diagnostics
## Appendix Table
```

The first is narrative diagnostic output. The second remains the default 11-column table.

The 14-column diagnostic table is not currently inserted into reports.

## Current CLI Relationship

The diagnostic formatter is not currently exposed as a CLI output selector or file-output command.

Task 034C selects a staged delivery contract:

```text
Task 034D: opt-in diagnostic-table stdout and explicit file output
later reviewed task: report composition, if needed
```

Proposed Task 034D selectors:

```text
--diagnostic-table
--output-diagnostic-table PATH
```

These options are contract proposals only until Task 034D is implemented and reviewed.

## Saved JSON Compatibility

The formatter accepts the existing preview dictionary contract. Saved preview JSON can represent:

```text
legacy/unavailable
eligible
no-eligible-obstacle
```

Invalid diagnostic states remain errors. The preview JSON schema is not changed by the formatter or Task 034C.

## Scoring and Product Invariants

The diagnostic table does not change:

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

Diagnostics remain offline terrain/surface support information. They are not a full link budget, RF field validation, RSSI prediction, SINR prediction, packet-loss prediction, communication-success prediction, reconnaissance-success prediction, or flight-feasibility prediction.

## Task 034B Verification Record

Implementation evidence is recorded in:

```text
docs/handoff/task-034b-dominant-obstacle-diagnostic-appendix-table-implementation.md
docs/paper/experiments/EXP-20260714-048-dominant-obstacle-diagnostic-appendix-table-implementation.md
```

Task 034C does not rerun or reclassify that local evidence.

## Task 034D Boundary

Expected source scope:

```text
src/uav_rf_terrain/preview_cli.py
```

Preferred focused test:

```text
tests/test_diagnostic_appendix_cli_output.py
```

Task 034D should not modify the formatter, report, preview schema, scoring, routing, waypoint, map, or UI modules unless a concrete blocker is demonstrated and reviewed before scope expansion.

## Non-Goals

This contract does not authorize:

- changing either table schema;
- changing report content in Task 034D;
- changing JSON or plain-text preview output;
- changing scoring, color, ranking, route, or waypoint behavior;
- adding map or UI rendering;
- accessing real DEM/DSM, GIS, QGIS, or `METADATA_MAP` data;
- committing generated output artifacts;
- adding external-device, autopilot, vehicle-control, or flight-control output.
