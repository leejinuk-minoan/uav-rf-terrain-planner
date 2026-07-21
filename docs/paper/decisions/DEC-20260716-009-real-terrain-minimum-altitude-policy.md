# DEC-20260716-009 - Real-Terrain Minimum-Altitude Policy

## Status

Approved by GPT Master.

## Date

2026-07-20

## Related Task / Issue / PR

Task 036A, Issue #108, merged PR #109.

## Decision Owner

GPT Master owns approval and research interpretation. Codex records the audited
implementation boundary and local verification evidence only.

## Proposed Decision

The future real-terrain altitude analyzer consumes a complete
`RealTerrainRouteResult`, an authoritative `SelectedLaunchSiteRecord`, one
exact-parity `TerrainDataAdapter` session, and dedicated bounded DSM/DEM radial
profiles. It returns one comparison-only minimum required constant-route MSL per
source route candidate, plus a separate all-route-sample current fixed-AGL baseline
assessment.

The selected record's projected point is the actual radial-profile origin.
`route_result.launch_ground_msl_m` is the DEM sampled at that actual point, not at
the snapped graph node. The actual-to-snapped connector is evaluated by the radial
profile to the first snapped route sample.

The proposed session sequence is fixed: validate route/selected/config/frequency/MGRS
authority without terrain access; open exactly one session; before any `sample_point`
or `extract_profile`, verify exact-policy `session.metadata ==
route_result.terrain_metadata`; sample the actual selected point to verify DEM parity
with `launch_ground_msl_m` within tolerance; then verify DSM occupancy below launch
antenna MSL; run route and aggregate radial guards; then begin route and radial sampling. Any
metadata, ground-parity, or occupancy failure is fatal before profile extraction.

The route result owns route order, source 3D totals, frequency, allowed AGL, terrain
metadata, snapped endpoints, actual launch ground, and snap distances. The selected
record must match its selected candidate ID and launch MGRS, including exact projected
point-to-MGRS conversion. Terrain sampling is permitted only if session metadata
exactly matches `route_result.terrain_metadata`; geometry compatibility alone is not
sufficient.

## Context

Task 015 provides a synthetic single-profile endpoint inversion. Tasks 035EF and 035G
provide complete route/handoff authority and MGRS-facing reports, but graph vertices
and report interpolation are not dense DSM/DEM clearance profiles. Task 035EF retains
the distinction between the actual selected launch point and a potentially different
snapped graph node, so the future altitude boundary must retain that distinction too.

## Rationale

This proposed hybrid contract prevents report-oriented data or geometry-compatible but
different datasets from being interpreted as clearance evidence. Constant MSL gives
one reviewable proxy value without terrain-following or per-waypoint flight commands.
The independent fixed-AGL assessment avoids inferring present-route sufficiency from
only the constant-MSL limiting sample. The 0.6 ratio remains an initial proxy default,
not a measured link-performance threshold.

## Alternatives Considered

- Complete route result only: rejected because handoffs are not dedicated profiles.
- Waypoint result only: rejected because 500 m interpolation has reporting semantics.
- Handoff tuples only: rejected because route/mission/metadata authority is lost.
- Dedicated profile only: rejected because it cannot prove source-route parity.
- Route result plus dedicated profiles: rejected because actual-launch versus snapped
  launch authority remains ambiguous.
- Complete route result, selected launch record, exact-parity session, and dedicated
  profiles: proposed.

## Contract Consequences

- `source_total_distance_3d_m` is source identity/parity only; horizontal sampling,
  guards, and ties use explicit `_2d_m` route and radial fields.
- Constant-MSL limiting and current-AGL deficit-limiting samples are separate.
- Every route sample receives a current clearance margin. The route result exposes the
  minimum margin and `current_fixed_agl_meets_proxy`.
- AGL over highest route DEM and target DEM is nonnegative by contract, normalized to
  zero within tolerance, and never display-clamped from a negative raw value.
- Metadata mismatch fails before sampling with `terrain session metadata does not
  match source route terrain authority`.
- Exact metadata parity is evaluated after the sole session opens and before its first
  terrain sample; it is not a pre-session metadata lookup.

## Impacted Documents

- `docs/architecture/real-terrain-minimum-altitude-boundary.md`
- `docs/handoff/task-036a-real-terrain-minimum-altitude-contract.md`
- `docs/paper/experiments/EXP-20260716-057-real-terrain-minimum-altitude-contract-audit.md`
- `docs/master-plan.md`
- `docs/research/research-index.md`
- `docs/paper/RESEARCH_BUILD_RECORD.md`

## Paper Boundary

The future output is an offline DSM/LOS/Fresnel clearance proxy. It is not evidence
of obstacle absence, communication success, flight feasibility, reconnaissance
success, approval, or authorization. The clearance ratio and synthetic verification
are methodological assumptions, not calibrated performance evidence.

## Product / Deployment Boundary

No UI, route-selection change, device integration, autopilot command, Android/TMMR
work, workflow, dependency, or GIS artifact is introduced by this proposed decision.

## Public Repository Sensitivity Check

No raster, generated output, private path, actual operational coordinate, credential,
or external-device instruction is recorded.

## Safety / Non-goals

The contract does not define a safe or approved altitude, guaranteed communications,
a flight-ready path, or regulatory guidance. It does not implement the future runtime.

## Follow-up Tasks

1. Obtain GPT Master approval after exact-head CI and review resolution.
2. Implement the separate bounded real-terrain altitude module with TDD.
3. Add synthetic and local adapter smoke evidence without committing GIS data.
4. Review human-facing report wording and field-validation limits separately.
