# DEC-20260716-009 - Real-Terrain Minimum-Altitude Policy

## Status

Approved contract for a future implementation task.

## Date

2026-07-20

## Related Task / Issue / PR

Task 036A, Issue #108, Draft PR pending creation.

## Decision Owner

GPT Master defines research interpretation; Codex records the audited implementation
boundary and local verification evidence.

## Decision

Future real-terrain altitude analysis consumes a complete `RealTerrainRouteResult`
plus one `TerrainDataAdapter` session and dedicated bounded DSM/DEM radial profiles.
It returns a comparison-only minimum required constant-route MSL for each source route
candidate. The source route result owns mission frequency, fixed AGL, route order,
totals, launch ground, snap, and terrain metadata. Dedicated profiles provide terrain
clearance evidence; waypoint-report interpolation is not reused for that purpose.

## Context

Task 015 provides a synthetic single-profile endpoint inversion. Tasks 035EF and 035G
now provide complete route/handoff authority and MGRS-facing reports, but their graph
vertices and reporting interpolation are not dense DSM/DEM clearance profiles. A
future implementation needs both authorities without changing existing route, waypoint,
score, or legacy synthetic behavior.

## Rationale

This hybrid boundary prevents sparse/report-oriented data from being interpreted as
clearance evidence while preserving immutable route and mission parity. A constant MSL
per route gives one reviewable proxy value without creating terrain-following or
per-waypoint flight commands. The 0.6 default remains an initial clearance proxy,
not a measured link-performance threshold.

## Alternatives Considered

- Complete route result only: rejected because handoffs are not dedicated profiles.
- Waypoint result only: rejected because 500 m interpolation has reporting semantics.
- Handoff tuples only: rejected because route/mission/metadata authority is lost.
- Dedicated profile only: rejected because it cannot prove source-route parity.
- Complete route authority plus dedicated profiles: selected.

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
work, workflow, dependency, or GIS artifact is introduced by this decision.

## Public Repository Sensitivity Check

No raster, generated output, private path, actual operational coordinate, credential,
or external-device instruction is recorded.

## Safety / Non-goals

The contract does not define a safe altitude, an approved altitude, guaranteed
communications, a flight-ready path, or regulatory guidance. It does not implement
the future runtime.

## Follow-up Tasks

1. Implement the separate bounded real-terrain altitude module with TDD.
2. Add synthetic and local adapter smoke evidence without committing GIS data.
3. Review human-facing report wording and field-validation limits separately.
