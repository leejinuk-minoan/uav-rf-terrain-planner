# Dominant Obstacle Diagnostic Appendix-Table Output Boundary

## Purpose

This document defines the reviewed contract for an optional Markdown appendix table that exposes the dominant Fresnel obstacle diagnostic fields already available in candidate preview records.

Task 034A is a documentation and code-contract audit only. It does not implement or change source code, tests, runtime formatters, CLI behavior, report composition, scoring, color classification, candidate ranking, route cost, waypoint cost, map rendering, or UI behavior.

## Live Baseline

Task 034A started after the required gate was verified:

```text
PR #87: merged
PR #87 merge commit: 740d3a5ee5e8edec2c3de3cff9e83265ee740dc5
Issue #86: closed / completed
Task 033C: complete
Issue #88: open
base main SHA: 740d3a5ee5e8edec2c3de3cff9e83265ee740dc5
```

## Current Default Appendix Table

The implemented default API is:

```python
format_preview_appendix_table(
    preview: Mapping[str, object],
    *,
    max_rows: int | None = None,
) -> str
```

Its exact columns are:

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

The current formatter:

- preserves candidate input order;
- assigns one-based deterministic `row_no` values to visible rows;
- validates `max_rows` as `None` or a positive non-boolean integer;
- uses `... N additional row(s) omitted.` when rows are omitted;
- rejects empty preview records;
- requires MGRS as the external coordinate format;
- rejects internal coordinate keys;
- does not mutate the input;
- does not create files;
- ignores non-internal diagnostic extra keys.

## Compatibility Decision

The default formatter remains byte-contract compatible.

Task 034B must not change the signature, columns, column order, cell formatting, validation sequence, row numbering, omission wording, input mutation behavior, or file-persistence behavior of `format_preview_appendix_table(...)`.

In particular, the default table continues to ignore diagnostic extras. Invalid diagnostic extras do not become a new failure mode for the default table. Diagnostic-aware validation belongs only to the new opt-in diagnostic formatter.

## Alternatives Compared

| Alternative | Compatibility | API clarity | Table readability | Validation/test complexity | Decision |
|---|---|---|---|---|---|
| A. Separate diagnostic appendix formatter | Preserves the default table exactly | Explicit intent and output contract | Wide table is isolated from the normal appendix | Reuses existing preview and diagnostic validators with focused tests | Selected |
| B. Opt-in flag on the existing formatter | Default can remain unchanged, but one function owns two incompatible schemas | Mode-dependent signature and branching | Caller must know which header contract applies | Larger regression surface and ambiguous downstream snapshots | Rejected |
| C. Directly expand the default table | Breaks existing header and downstream byte contract | Simple call surface | Makes every appendix table excessively wide | Existing tests, snapshots, docs, and callers change | Rejected |
| D. Do not expose diagnostics in appendix tables | No implementation risk | No new API | Report remains readable | Loses row-wise paper traceability and structured comparison value | Rejected |

## Selected API Boundary

Task 034B may add this new pure formatter in `src/uav_rf_terrain/preview_appendix_table.py`:

```python
def format_fresnel_diagnostics_appendix_table(
    preview: Mapping[str, object],
    *,
    max_rows: int | None = None,
) -> str:
    ...
```

The function:

- returns a Markdown table string;
- performs no file I/O;
- performs no coordinate conversion;
- performs no scoring or ordering changes;
- raises `PreviewAppendixTableError` for invalid preview or diagnostic states;
- reuses the existing base preview validation and `max_rows` contract;
- reuses `validate_flat_fresnel_diagnostics(...)` and `DIAGNOSTIC_FIELD_ORDER` from `fresnel_diagnostics.py`.

No new public error class is required.

## Exact Diagnostic Table Columns

The exact columns and order are:

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

All ten approved diagnostic values remain in one detailed table. The DSM MSL and LOS MSL fields are retained because the formatter is explicitly a diagnostic appendix, not the concise default table. Splitting them into a second detail table would introduce another schema, another row-subset contract, and extra composition complexity without adding information.

`dominant_obstacle_sample_index` is not included.

## Units and Precision

Units are encoded in the column names through `_m` and `_db` suffixes. Numeric cells contain values only; they do not append `m` or `dB` strings.

Human-readable formatting is:

| Field group | Cell format |
|---|---|
| `average_fresnel_score`, `worst_obstacle_score` | one decimal place |
| distance, DSM MSL, LOS MSL, clearance, Fresnel radius | one decimal place |
| clearance ratio | three decimal places |
| `nu` | three decimal places |
| diffraction loss | one decimal place |

This formatting affects only the returned Markdown string. Stored preview values, JSON values, analysis values, and scoring values remain unchanged.

## Diagnostic State Contract

The exact status strings are:

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

Absence is not interpreted as zero, clear path, or no obstacle.

### Enriched record with eligible obstacle

Condition:

```text
all ten diagnostic keys present
all ten values finite numeric
```

Output:

```text
diagnostic_status = eligible
all ten value cells use the approved precision
```

### Enriched record with no eligible interior obstacle

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

`not-applicable` is distinct from legacy `unavailable`. Neither state uses numeric zero.

### Invalid states

The following produce `PreviewAppendixTableError` before any table is returned:

```text
partial diagnostic key set
mixed numeric/null obstacle values
boolean numeric value
NaN
positive infinity
negative infinity
```

Invalid states do not receive status labels or output rows.

## Ordering and `max_rows`

The diagnostic formatter follows the default table contract:

- input candidate order is preserved;
- visible rows are the first `max_rows` records, or all records when `max_rows is None`;
- `row_no` starts at 1 for the visible subset;
- invalid `max_rows` values are rejected;
- omitted rows use the exact suffix `... N additional row(s) omitted.`;
- empty record input is rejected;
- input is not mutated;
- no file is created.

When callers invoke the default and diagnostic formatters with the same preview and the same `max_rows`, both tables represent the same candidate subset in the same order.

## Coordinate Boundary

The only user-facing candidate coordinate remains:

```text
candidate_cell_mgrs
external_coordinate_format = MGRS
```

The formatter must reject or exclude:

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

`dominant_obstacle_distance_from_start_m` is a scalar distance along the analyzed candidate-to-target path. It is not an independent map coordinate.

## Validation Reuse

Task 034B should avoid a second diagnostic state machine.

Recommended reuse:

```text
preview_appendix_table.py
- existing base preview validation
- existing max_rows validation
- existing Markdown escaping helpers

fresnel_diagnostics.py
- DIAGNOSTIC_FIELD_ORDER
- validate_flat_fresnel_diagnostics(record)
```

The new formatter should translate `CandidateFresnelDiagnosticsError` into `PreviewAppendixTableError` with the existing appendix-table error boundary.

`candidate_display_preview.py` and `preview_report.py` should not be refactored merely to implement this table. A shared formatting helper should be extracted only if a verified duplication defect appears during Task 034B review.

## Report Relationship

The current report already provides a deterministic `## Fresnel Diagnostics` narrative section and includes the existing default appendix table.

Task 034B does not automatically insert the new diagnostic table into reports and does not change `format_preview_report(...)`.

Any future report composition option requires a separate reviewed task because it changes report length, section content, and output snapshots.

## CLI Relationship

Task 034B does not add or change CLI options.

The proposed formatter is a pure Python API. A future CLI or explicit file-output surface for the diagnostic table requires a separate boundary and implementation task.

## Scoring and Product Invariants

The contract does not change:

```text
dsm_fresnel_score == average_fresnel_score
shielding_stability_score = dsm_los_score * 0.40 + dsm_fresnel_score * 0.60
overall_score = shielding_stability_score * 0.80 + distance_score * 0.20
strict LOS cap when dsm_los_score == 0
color thresholds
candidate order or ranking
route cost
waypoint cost
```

Diagnostics remain offline terrain/surface support information. They are not a full link budget, RSSI prediction, SINR prediction, packet-loss prediction, communication-success prediction, reconnaissance-success prediction, flight-feasibility prediction, or field RF validation.

Map rendering and UI visualization remain out of scope.

## Task 034B Candidate Scope

Likely source change:

```text
src/uav_rf_terrain/preview_appendix_table.py
```

Likely focused tests:

```text
tests/test_preview_appendix_table.py
tests/test_dominant_obstacle_preview_integration.py
```

`preview_report.py`, `candidate_display_preview.py`, and `fresnel_diagnostics.py` should remain unchanged unless a concrete integration blocker is demonstrated before expanding scope.

The Task 034B test matrix must cover:

```text
default table exact regression
legacy diagnostic table
eligible diagnostic table
no-eligible diagnostic table
partial-key rejection
mixed-null rejection
bool rejection
NaN/infinity rejection
exact columns and order
precision
unavailable/not-applicable strings
candidate order
max_rows and omission wording
input immutability
internal-coordinate rejection
sample-index non-exposure
no file creation
saved JSON compatibility
score/color/rank/route/waypoint invariance
```

## Non-Goals

Task 034A and the proposed Task 034B contract do not authorize:

- modifying the default appendix table;
- adding a CLI option;
- adding a report section or automatic report table;
- changing preview JSON schema;
- changing scoring, color, ranking, route, or waypoint behavior;
- adding map or UI rendering;
- accessing real DEM/DSM, GIS, QGIS, or `METADATA_MAP` data;
- committing generated JSON, report, table, image, PDF, CSV, or archive artifacts;
- producing external-device, autopilot, vehicle-control, or flight-control output.
