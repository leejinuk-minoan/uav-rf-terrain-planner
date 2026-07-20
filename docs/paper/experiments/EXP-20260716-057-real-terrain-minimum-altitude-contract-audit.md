# EXP-20260716-057 - Real-Terrain Minimum-Altitude Contract Audit

## Date

2026-07-20

## Related Task / Issue / PR

Task 036A, Issue #108, Draft PR #109.

## Experiment Purpose

Audit the legacy synthetic altitude scaffold and completed real-terrain route/waypoint
contracts to propose a future implementation boundary without adding runtime behavior.

## Input Data

Repository source and documentation only: synthetic `TerrainProfile` fixtures, the
legacy `minimum_altitude.py` API, Task 035EF complete route outputs and selected launch
records, Task 035G waypoint outputs, terrain policy, and MGRS boundary records. No
local GIS raster, actual coordinate, generated artifact, field RF measurement, or
flight data is used.

## Scenario / Configuration

The audit compares complete route authority, actual selected-launch authority,
waypoint-report records, handoffs, and dedicated profile sampling for route-level
minimum required constant MSL. The proposed ratio default is 0.6 with an allowed
`[0, 1]` interval and a source-authoritative frequency.

## Method

1. Read the legacy synthetic inversion and focused tests.
2. Trace actual launch ground, selected point, snapped graph origin, frequency, fixed
   AGL, 3D route totals, terrain metadata, handoffs, and MGRS through Task 035EF.
3. Compare route-only, waypoint, handoff, profile-only, and selected-launch hybrid
   input architectures against authority, parity, mathematical meaning, and safety.
4. Freeze exact terrain-session metadata parity, separate 2D sampling from 3D source
   totals, radial profile guards, constant-MSL inversion, independent current fixed-AGL
   margins, nonnegative AGL invariants, schemas, warnings, and fatal boundaries.

## Expected Result

One unambiguous future input and altitude model is proposed without altering the
legacy API, current route/waypoint behavior, dependencies, workflow, or GIS data.

## Actual Result

The audit proposes complete `RealTerrainRouteResult` authority plus an authoritative
`SelectedLaunchSiteRecord`, one exact-parity terrain session, and dedicated bounded
radial DSM/DEM profiles from the actual selected launch point. The primary future
output is one comparison-only constant MSL per source route. Every route sample also
receives an independent current fixed-AGL clearance margin. Waypoint interpolation was
explicitly rejected as terrain-clearance evidence.

## Metrics

- Runtime source files added or changed: 0.
- Existing legacy minimum-altitude focused test file retained unchanged.
- Contract alternatives compared: 6.
- Selected primary altitude semantics: 1 constant-MSL result plus 1 independent
  fixed-AGL baseline assessment.

## CI / Local Test Result

The Task 036A required commands are regression checks only because source and tests
are unchanged. Before this amendment, local `compileall`, Ruff, mypy, and diff checks
passed; the legacy minimum-altitude focused suite passed 19 tests and the full suite
passed 913 with 1 skip. Fresh amendment-head evidence belongs in the PR completion
comment and completion report under the non-recursive ledger policy.

## Interpretation

The audit establishes a proposed software/research contract. It does not establish
actual terrain clearance, communication performance, operational route suitability,
flight feasibility, or approval outcome.

## Limitations

No runtime module, GIS-backed smoke, browser/UI validation, field RF measurement, or
flight test is included. The 0.6 ratio is a proxy default rather than a calibrated
physical performance threshold. DEC-009 remains proposed pending GPT Master approval.

## Paper Figure / Table Candidate

Potential methods table: selected-launch/route/session authority and the 2D/3D
distance distinction. Potential formula table: radial-profile inversion, separate
constant-MSL and fixed-AGL limiting samples, and nonnegative AGL invariants. Neither
is operational performance evidence.

## Public Repository Sensitivity Check

No GIS/PDF/generated artifact, private path, actual operational coordinate,
credential, external-device instruction, or autopilot content is committed.

## Follow-up Tasks

Obtain GPT Master approval, implement and test the separate future runtime, then
collect local adapter smoke and separately review field-validation and human-report
limits.
