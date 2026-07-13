# Dominant Obstacle Preview and Report Output Boundary

## Purpose

This document records the reviewed preview, JSON, plain-text, report, and default appendix-table boundary for dominant Fresnel obstacle diagnostics.

Task 033A defined the optional output contract. Task 033B implemented the candidate-to-preview/report projection on `main` through PR #85. Task 034A defines a separate future diagnostic appendix-table contract without implementing it.

## Current Implemented Path

```text
FresnelAnalysis
→ CandidateFresnelDiagnostics
→ SyntheticCandidateRecord
→ CandidateCellMapFeature
→ CandidateDisplayRecord
→ preview dictionary
→ plain text / JSON / report
```

The approved optional flat record fields are exactly:

```text
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

`dominant_obstacle_sample_index` remains internal.

## Compatibility States

### Legacy or un-enriched record

```text
all diagnostic keys absent
```

This remains valid. Absence means diagnostics are unavailable; it is not zero, a clear path, or a no-obstacle result.

### Enriched record with eligible obstacle

```text
all ten diagnostic keys present
all ten values finite numeric
```

### Enriched record with no eligible interior obstacle

```text
all ten diagnostic keys present
average_fresnel_score finite numeric
remaining nine values null
```

### Invalid record

The following are rejected by diagnostic-aware paths:

```text
partial key set
mixed numeric/null obstacle values
boolean numeric value
NaN
positive or negative infinity
```

## JSON Boundary

JSON stdout and file output preserve original float precision. The valid no-eligible state uses JSON `null` for the nine obstacle-detail values.

No human-readable rounding is applied to JSON values.

## Plain-Text Boundary

The default plain-text preview may show the concise diagnostic subset:

```text
average Fresnel score
worst obstacle score
diffraction loss
```

Human-readable score and loss values use one decimal place. No-eligible values are described as unavailable in the existing concise preview surface.

## Report Boundary

The report includes a deterministic section:

```text
## Fresnel Diagnostics
```

It preserves candidate order, identifies candidates by `candidate_id` and `candidate_cell_mgrs`, distinguishes legacy unavailable data from a valid no-eligible result, and uses the approved display precision.

`--report` and `--output-report PATH` use the same report formatter content contract.

## Current Default Appendix Table Boundary

The implemented default formatter remains:

```python
format_preview_appendix_table(
    preview,
    *,
    max_rows=None,
)
```

Its columns remain exactly:

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

Task 033B intentionally left these columns unchanged. The default formatter ignores diagnostic extra keys and does not become diagnostic-aware.

Task 034A preserves this default output as byte-contract compatible.

## Task 034A Diagnostic Appendix Contract

Task 034A selects a separate future pure formatter rather than an opt-in flag or direct expansion of the default table.

The detailed contract is defined in:

```text
docs/architecture/dominant-obstacle-appendix-table-output-boundary.md
```

Proposed future API:

```python
format_fresnel_diagnostics_appendix_table(
    preview,
    *,
    max_rows=None,
)
```

Task 034A does not implement this function. Task 034B remains a separate future Local implementation task.

The proposed diagnostic table has its own exact 14-column schema, deterministic status strings, unavailable/null display strings, precision rules, and the same candidate subset and `max_rows` behavior as the default table.

## Report and CLI Separation

Task 034B must not automatically insert the diagnostic table into `format_preview_report(...)`.

Task 034B must not add CLI options or file-output commands.

Future report composition or CLI/file-output support requires another reviewed boundary because those changes affect output snapshots and public interfaces.

## Display Precision

Human-readable preview, report, and proposed diagnostic table formatting use:

| Value | Display precision |
|---|---|
| score | 1 decimal place |
| distance, elevation, clearance, Fresnel radius | 0.1 m |
| clearance ratio | 3 decimal places |
| knife-edge `nu` | 3 decimal places |
| diffraction loss | 0.1 dB |

These rules do not alter stored values, JSON values, or scoring inputs.

## Coordinate Boundary

The user-facing candidate coordinate remains:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
```

The following remain internal and must not be exposed:

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
dominant_obstacle_sample_index
```

`dominant_obstacle_distance_from_start_m` is a path-relative scalar, not an independent map coordinate.

## Scoring and Ordering Invariants

The output contracts do not change:

```text
dsm_fresnel_score = average_fresnel_score
shielding_stability_score = dsm_los_score × 0.40 + dsm_fresnel_score × 0.60
overall_score = shielding_stability_score × 0.80 + distance_score × 0.20
strict LOS cap when dsm_los_score == 0
color classification thresholds
candidate order or ranking
route cost
waypoint cost
```

No separate DSM surface-complexity score is part of the current default shielding score.

## Interpretation Boundary

Dominant obstacle and single knife-edge loss values are terrain/surface diagnostic proxies only.

They are not:

```text
full link-budget reconstruction
measured RF validation
RSSI prediction
SINR prediction
packet-loss prediction
communication-success prediction
reconnaissance-success prediction
flight-feasibility prediction
```

Map rendering and UI visualization remain outside these output contracts.

## Follow-Up Tasks

1. Task 034B may implement only the separate pure diagnostic appendix formatter and focused tests.
2. Report composition requires a separate reviewed task.
3. CLI or explicit file-output support requires a separate reviewed task.
4. Scoring, color, ranking, route, waypoint, map, or UI use requires separate validation and explicit approval.
5. Field RF validation remains future research.
