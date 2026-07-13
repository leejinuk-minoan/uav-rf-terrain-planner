# Dominant Obstacle Preview and Report Output Boundary

## Purpose

This document defines the reviewed output contract for exposing the dominant Fresnel obstacle diagnostics implemented by Task 032CD as optional preview and report information.

Task 033A is documentation and contract audit only. It does not change source code, tests, runtime preview schema, formatter behavior, CLI behavior, scoring, color classification, candidate ordering, route cost, or waypoint cost.

## Current Implemented Analysis

`src/uav_rf_terrain/fresnel.py` currently provides:

```text
FresnelAnalysis.average_fresnel_score
FresnelAnalysis.worst_obstacle_score
FresnelAnalysis.dominant_obstacle
```

`dsm_fresnel_score` retains its historical arithmetic-mean meaning and equals `average_fresnel_score`.

`DominantFresnelObstacle` contains the selected eligible interior sample's path-relative geometry, clearance, sample score, knife-edge parameter, and additional single knife-edge diffraction-loss proxy.

## Current Object Transfer Path and Gap Audit

The currently implemented preview path is:

```text
build_synthetic_candidate_records()
→ SyntheticCandidateRecord
→ build_candidate_cell_map_features()
→ CandidateCellMapFeature
→ build_candidate_display_records()
→ CandidateDisplayRecord
→ build_candidate_display_preview_dict()
→ preview dictionary
→ plain-text / JSON / appendix table / report
```

The Fresnel diagnostic analysis exists on a separate path:

```text
analyze_dsm_fresnel(...)
→ FresnelAnalysis
```

There is currently no implemented bridge from `FresnelAnalysis` into the candidate preview path.

| Stage | Current file and object/function | Diagnostic state | Task 033B minimum change point |
|---|---|---|---|
| Fresnel analysis | `src/uav_rf_terrain/fresnel.py`: `FresnelAnalysis`, `DominantFresnelObstacle`, `analyze_dsm_fresnel(...)` | Values exist | Preserve the nested analysis model; do not change scoring semantics |
| Candidate/scenario | `src/uav_rf_terrain/scenario_outputs.py`: `SyntheticCandidateRecord`, `build_synthetic_candidate_records()` | Only scalar scoring inputs and `CandidateScore` are carried; no `FresnelAnalysis` or diagnostic projection | Add an optional diagnostic projection source for enriched synthetic/current candidate records, without requiring it for legacy records |
| Map feature | `src/uav_rf_terrain/map_outputs.py`: `CandidateCellMapFeature`, `build_candidate_cell_map_features(...)` | Overall and shielding scores are copied; diagnostics are omitted | Add dedicated optional diagnostic fields or a dedicated diagnostic mapping; do not overload source-zone metadata |
| Display record | `src/uav_rf_terrain/candidate_display_outputs.py`: `CandidateDisplayRecord`, `to_display_dict()`, `build_candidate_display_records(...)` | Fixed display fields only; diagnostics are omitted | Add the all-or-none optional flat diagnostic field set and validation |
| Preview object/dictionary | `src/uav_rf_terrain/candidate_display_preview.py`: `CandidateDisplayPreview`, `build_candidate_display_preview_dict(...)` | Display dictionaries are copied; current primitive-value validation allows `str`, `float`, and `bool`, but not `None` | Expand the reviewed optional-value contract to permit diagnostic `None` only in the defined enriched no-obstacle state; reject partial sets |
| Plain text | `format_candidate_display_preview(...)` | Current line contains candidate label, overall score, and source zone only | Add a concise diagnostic summary when enriched; keep legacy lines valid |
| JSON stdout/file | `preview_cli.py` uses the preview dictionary | Diagnostics are absent | Serialize the optional flat field set unchanged, preserving float precision |
| Appendix table | `preview_appendix_table.py`: `format_preview_appendix_table(...)` | Fixed columns; extra non-internal keys are not displayed | Do not add columns in Task 033B; retain current table contract |
| Report | `preview_report.py`: `format_preview_report(...)` | Uses current preview/table validation and fixed sections; no diagnostic section | Add dedicated optional diagnostic validation and `## Fresnel Diagnostics`; legacy preview remains valid |
| Report CLI/file | `preview_cli.py`: `--report`, `--output-report` | Both consume the same report formatter | No separate report content contract; both surfaces must remain identical |

The primary gap is therefore not inside `FresnelAnalysis`; it is the absence of a reviewed optional projection across candidate, map, display, and preview records.

## Optional Flat Projection

Task 033B should project the nested analysis data into this exact optional user-facing record field set:

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

`dominant_obstacle_sample_index` remains an internal diagnostic and is excluded from default user-facing preview and report records.

The projection is flat so saved JSON remains straightforward to validate and downstream formatters do not need to reconstruct or serialize the nested dataclass.

## Backward Compatibility and Validation

### Legacy or un-enriched preview

```text
diagnostic field set entirely absent
```

Policy:

- existing saved JSON remains valid;
- current table and report paths remain usable;
- no diagnostic value is inferred;
- report wording may state: `diagnostics unavailable in this preview record`.

Absence means unavailable data, not a zero score or a clear path.

### Enriched preview with an eligible dominant obstacle

```text
all diagnostic fields present
average_fresnel_score = finite numeric
worst_obstacle_score = finite numeric
dominant obstacle detail fields = finite numeric
```

The values are copied from the existing analysis result. They do not trigger score or order changes.

### Enriched preview with no eligible interior dominant obstacle

```text
all diagnostic fields present
average_fresnel_score = finite numeric
worst_obstacle_score = null
all dominant obstacle detail fields = null
```

Recommended report wording:

```text
no eligible interior dominant obstacle sample
```

This state is distinct from a legacy preview where the entire field set is absent.

### Partial diagnostic field set

A record containing only some diagnostic keys is invalid.

Rationale:

- partial records cannot reliably distinguish missing data from a no-obstacle result;
- report and JSON consumers would otherwise infer inconsistent meanings;
- an all-or-none key-set rule preserves deterministic validation;
- legacy records remain valid because the complete set may be absent.

Task 033B should validate this policy before report/file output. The appendix table should continue to validate its existing required fields and ignore approved diagnostic extras rather than add new columns.

## Output Surface Policy

### JSON stdout and JSON file

- include the optional flat fields when the record is enriched;
- preserve the original Python float values through JSON serialization;
- use JSON `null` for the reviewed no-eligible-obstacle state;
- do not apply human-readable rounding;
- do not add internal sample indices or internal coordinates.

### Default plain-text preview

Keep output concise. For enriched records, the recommended summary is:

```text
average_fresnel_score=<0.1>
worst_obstacle_score=<0.1 or unavailable>
diffraction_loss_db=<0.1 dB or unavailable>
```

Legacy records remain unchanged or receive a concise unavailable marker only if that does not make the default output excessively verbose.

### Report stdout and report file

Add a deterministic section:

```text
## Fresnel Diagnostics
```

The section should:

- preserve candidate record order;
- identify each candidate by `candidate_id` and `candidate_cell_mgrs`;
- distinguish legacy unavailable diagnostics from an enriched no-eligible-obstacle result;
- display the reviewed diagnostic values with human-readable precision;
- explain that the values are diagnostic proxies only.

`--report` and `--output-report PATH` use the same `format_preview_report(...)` contract and therefore must contain identical report content apart from destination handling.

### Appendix table

Task 033B should not change existing appendix table columns, order, row-limit behavior, or table formatter semantics.

A future reviewed table-extension task may decide whether diagnostic columns belong in a separate table or an expanded appendix format.

## Display Precision

JSON retains original float precision.

Plain-text and report surfaces use:

| Value | Display precision |
|---|---|
| score | 1 decimal place |
| distance, elevation, clearance, Fresnel radius | 0.1 m |
| clearance ratio | 3 decimal places |
| knife-edge `nu` | 3 decimal places |
| diffraction loss | 0.1 dB |

These are display rules only and must not round stored or scored values.

## Coordinate and Metadata Boundary

User-facing candidate coordinates remain:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
```

The following remain internal and must not appear in preview/report records:

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
```

`dominant_obstacle_distance_from_start_m` is a scalar distance along the analyzed path. It is not a map coordinate and must not be interpreted as a location independent of the candidate-to-target path.

`source_zone`, `source_sensitive`, and `source_zone_reason` remain interpretation metadata. They do not modify dominant-obstacle selection, diffraction-loss calculation, candidate scoring, or ranking.

## Scoring and Ordering Invariants

Task 033B must not change:

```text
dsm_fresnel_score = average_fresnel_score
shielding_stability_score = dsm_los_score × 0.40 + dsm_fresnel_score × 0.60
overall_score = shielding_stability_score × 0.80 + distance_score × 0.20
strict LOS cap when dsm_los_score == 0
color classification thresholds
candidate record order or ranking
route cost
waypoint cost
```

No separate DSM surface-complexity or obstacle score is part of the current default shielding score.

The dominant obstacle and single knife-edge loss are additional terrain/surface diagnostic proxies. They are not a full link budget and do not predict RSSI, SINR, packet loss, communication success, reconnaissance success, or flight feasibility.

## Task 033B Recommended Scope

A narrow Local implementation should review changes to:

```text
src/uav_rf_terrain/scenario_outputs.py
src/uav_rf_terrain/map_outputs.py
src/uav_rf_terrain/candidate_display_outputs.py
src/uav_rf_terrain/candidate_display_preview.py
src/uav_rf_terrain/preview_report.py
focused preview/report tests
```

`fresnel.py`, scoring, classification, routing, waypoint calculation, appendix-table columns, and CLI options should remain unchanged unless a verified integration blocker is reported before implementation.

Task 033B should add focused tests for legacy, enriched-with-obstacle, enriched-without-obstacle, partial-set rejection, JSON precision, plain-text precision, report section ordering, internal-coordinate exclusion, table compatibility, no mutation, and existing-mode regression.

## Non-Goals

Task 033A and the proposed Task 033B boundary do not define:

- full link-budget reconstruction;
- measured RF validation;
- RSSI, SINR, or packet-loss prediction;
- communication or flight outcome guarantees;
- MGRS conversion or geographic validation;
- map, card, popup, HTML, or PDF rendering;
- scoring, color, ranking, route, or waypoint changes;
- real DEM/DSM or `METADATA_MAP` access;
- external-device, autopilot, or flight-control output.
