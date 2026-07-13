# DEC-20260713-002 - Dominant Obstacle Diagnostic Output Policy

## Decision

Dominant Fresnel obstacle values are approved for future exposure as optional preview and report diagnostic information.

They are not approved for candidate scoring, color classification, ordering/ranking, route cost, or waypoint cost.

## Context

Task 032CD added:

```text
average_fresnel_score
worst_obstacle_score
dominant_obstacle
```

The current candidate preview path does not carry those values. A reviewed output boundary is required before runtime schema or formatter changes.

## Approved Projection

Task 033B should use an optional flat projection rather than serializing the nested `DominantFresnelObstacle` dataclass directly.

The approved user-facing key set is:

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

## Compatibility Decision

Legacy preview records with the entire diagnostic set absent remain valid.

Enriched records must contain the complete field set. Partial diagnostic sets are invalid.

If no eligible interior sample exists, `average_fresnel_score` remains finite while `worst_obstacle_score` and all dominant-obstacle detail fields are null.

## Output-Surface Decision

- JSON may expose the optional flat fields without human-readable rounding.
- Plain-text preview may show a concise average/worst/loss summary.
- Report output should add `## Fresnel Diagnostics`.
- `--report` and `--output-report` retain the same formatter content contract.
- Appendix table columns remain unchanged in Task 033B.

## Scoring Decision

The following remain unchanged:

```text
dsm_fresnel_score == average_fresnel_score
shielding_stability_score = dsm_los_score × 0.40 + dsm_fresnel_score × 0.60
overall_score = shielding_stability_score × 0.80 + distance_score × 0.20
strict LOS cap when dsm_los_score == 0
```

No separate DSM surface-complexity score is part of the current default score.

## Rationale

The diagnostic helps explain where the most restrictive eligible Fresnel sample occurs without changing the reviewed historical average score or downstream behavior.

Keeping the appendix table unchanged prevents one output extension from silently changing a separate fixed-column contract.

Maintaining legacy records avoids invalidating existing saved JSON and report/table workflows.

## Alternatives Considered

1. Replace the average Fresnel score with the worst score: rejected because it changes score semantics and ranking.
2. Add diffraction loss to overall scoring: rejected pending separate validation and explicit approval.
3. Serialize the nested dataclass directly: rejected in favor of a stable flat JSON contract.
4. Expand the appendix table in the same task: deferred to a separate reviewed task.

## Interpretation Boundary

Dominant obstacle and single knife-edge loss values are additional terrain/surface diagnostic proxies.

They are not a full link budget, measured RF result, RSSI estimate, SINR estimate, packet-loss estimate, communication-success prediction, reconnaissance guarantee, or flight-feasibility guarantee.

## Impacted Documents

```text
docs/architecture/dominant-obstacle-preview-report-output-boundary.md
docs/architecture/fresnel-dominant-obstacle-integration.md
docs/handoff/task-033a-dominant-obstacle-output-boundary-and-documentation-alignment.md
docs/paper/experiments/EXP-20260713-044-dominant-obstacle-output-boundary-review.md
```

## Public Repository Sensitivity Check

This decision contains repository contracts only. No private path, credential, terrain raster, GIS file, generated artifact, operational command, or device-control output is included.

## Follow-Up Tasks

Task 033B may implement the approved optional projection with focused backward-compatibility tests. Any appendix-table extension or scoring use requires another reviewed decision.
