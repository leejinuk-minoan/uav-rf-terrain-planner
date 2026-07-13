# Task 033A Dominant Obstacle Output Boundary and Documentation Alignment

## Purpose

Task 033A defines the optional preview/report output boundary for the dominant Fresnel obstacle diagnostics implemented by Task 032CD and reconciles current documentation with the implemented score model.

This is a documentation and code/document contract audit. It changes no runtime source, tests, schema, formatter, CLI behavior, scoring, color, ranking, route, waypoint, GIS, or device-control behavior.

## Current Verified State

- Base branch: `main`
- Base commit: `325a23a55351de303fab10a8462bb9b5464e5d65`
- PR #81: merged
- Implemented diagnostics: `average_fresnel_score`, `worst_obstacle_score`, `dominant_obstacle`
- Compatibility: `dsm_fresnel_score == average_fresnel_score`

## Documents Added

```text
docs/architecture/dominant-obstacle-preview-report-output-boundary.md
docs/handoff/task-033a-dominant-obstacle-output-boundary-and-documentation-alignment.md
docs/paper/decisions/DEC-20260713-002-dominant-obstacle-diagnostic-output-policy.md
docs/paper/experiments/EXP-20260713-044-dominant-obstacle-output-boundary-review.md
```

## Current Transfer-Path Finding

The implemented diagnostic exists in `FresnelAnalysis`, but the current preview path is built independently from synthetic scalar scores:

```text
FresnelAnalysis  [diagnostics exist]

build_synthetic_candidate_records()
→ SyntheticCandidateRecord
→ CandidateCellMapFeature
→ CandidateDisplayRecord
→ preview dictionary
→ plain-text / JSON / table / report
```

No current object bridge carries the nested dominant obstacle from `FresnelAnalysis` into `SyntheticCandidateRecord`, `CandidateCellMapFeature`, or `CandidateDisplayRecord`.

Additional verified gaps:

- `CandidateDisplayRecord.to_display_dict()` returns only the current fixed fields;
- `candidate_display_preview.py` currently permits `str`, `float`, and `bool` record values but not diagnostic `None`;
- the appendix table has fixed diagnostic-free columns;
- the report has no `## Fresnel Diagnostics` section;
- `--report` and `--output-report` already share the same report formatter contract.

## Output Contract Decision

Task 033B should use an optional all-or-none flat projection:

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

State policy:

1. Entire field set absent: legacy/un-enriched preview; keep valid.
2. Entire field set present with finite values: enriched preview with eligible obstacle.
3. Entire field set present with finite average and null worst/details: enriched preview with no eligible interior sample.
4. Partial field set: invalid.

## Surface Policy

- JSON: optional flat fields, original float precision, JSON null for reviewed no-obstacle state.
- Plain text: concise average/worst/diffraction summary.
- Report: new `## Fresnel Diagnostics` section with candidate-order preservation.
- Appendix table: no column or contract change in Task 033B.

## Scoring and Ordering Boundary

The following remain unchanged:

```text
dsm_fresnel_score meaning
LOS 0.40 / Fresnel 0.60 shielding weights
overall shielding 0.80 / distance 0.20 weights
strict LOS cap
color thresholds
candidate order/ranking
route cost
waypoint cost
```

A separate DSM surface-complexity score is not part of the current default score.

## Code/Test Change Check

```text
source files changed by Task 033A: 0
test files changed by Task 033A: 0
workflow files changed: 0
pyproject changes: 0
runtime schema changes: 0
formatter/CLI changes: 0
```

## Test and CI Result

The Cloud Agent does not claim local `pytest`, Ruff, mypy, compileall, CLI execution, preview generation, or report generation.

GitHub Actions is checked on the final Draft PR head and recorded in the completion report. The existing standard workflow remains unchanged.

## Public Repository Sensitivity Check

No private path, credential, real terrain data, `METADATA_MAP` content, raster, GIS file, QGIS project, generated preview/report artifact, image, PDF, CSV, archive, external-device command, or flight-control output is included.

## Limitations

Task 033A defines a future output contract. It does not prove that diagnostics are currently available in preview records and must not be read as runtime implementation.

The single knife-edge loss is an additional terrain/surface proxy, not a full link budget or measured communication result.

## Task 033B Recommendation

Implement the smallest reviewed diagnostic bridge across candidate, map, display, preview, and report layers. Preserve legacy saved JSON, reject partial diagnostic key sets, add no appendix-table columns, and leave scoring/classification/routing/waypoint logic unchanged.

Task 033B should run local focused and full regression tests and submit a separate PR.
