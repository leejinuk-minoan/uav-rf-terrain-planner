# EXP-20260716-057 - Real-Terrain Minimum-Altitude Contract Audit

## Date

2026-07-20

## Related Task / Issue / PR

Task 036A, Issue #108, Draft PR pending creation.

## Experiment Purpose

Audit the legacy synthetic altitude scaffold and completed real-terrain route/waypoint
contracts to freeze a future implementation boundary without adding runtime behavior.

## Input Data

Repository source and documentation only: synthetic `TerrainProfile` fixtures, the
legacy `minimum_altitude.py` API, Task 035EF complete route outputs, Task 035G waypoint
outputs, terrain policy, and MGRS boundary records. No local GIS raster, actual
coordinate, generated artifact, field RF measurement, or flight data is used.

## Scenario / Configuration

The audit compares complete route authority, waypoint-report records, handoffs, and
dedicated profile sampling for route-level minimum required constant MSL. The selected
future ratio default is 0.6 with an allowed `[0, 1]` interval and a source-authoritative
frequency.

## Method

1. Read the legacy synthetic inversion and focused tests.
2. Trace frequency, fixed AGL, launch ground, route totals, snap, metadata, handoff,
   and MGRS authority through Task 035EF and Task 035G.
3. Compare five possible input architectures against data availability, mathematical
   meaning, compatibility, public-output safety, testability, and research validity.
4. Freeze the selected hybrid profile model, MSL/AGL formulas, result schemas, guards,
   tie rule, warnings, fatal errors, and non-claims.

## Expected Result

One unambiguous future input and altitude model is selected without altering the
legacy API, current route/waypoint behavior, dependencies, workflow, or GIS data.

## Actual Result

The audit selected complete `RealTerrainRouteResult` authority plus dedicated bounded
radial DSM/DEM profiles from one terrain session. The primary future output is one
comparison-only constant MSL per available source route. Waypoint interpolation was
explicitly rejected as terrain-clearance evidence.

## Metrics

- Runtime source files added or changed: 0.
- Existing legacy minimum-altitude focused test file retained unchanged.
- Contract alternatives compared: 5.
- Selected primary altitude semantics: 1.

## CI / Local Test Result

The Task 036A required commands are regression checks only because source and tests
are unchanged. Their local and exact final-head CI outcomes are recorded in the PR
completion evidence under the non-recursive ledger policy.

## Interpretation

The audit establishes a reviewable software/research contract. It does not establish
actual terrain clearance, communication performance, operational route suitability,
flight feasibility, or approval outcome.

## Limitations

No runtime module, GIS-backed smoke, browser/UI validation, field RF measurement, or
flight test is included. The 0.6 ratio is a proxy default rather than a calibrated
physical performance threshold.

## Paper Figure / Table Candidate

Potential methods table: input-authority alternatives and selected hybrid data flow.
Potential formula table: radial-profile inversion, limiting-sample tie rule, and raw
versus display-clamped AGL. Neither is operational performance evidence.

## Public Repository Sensitivity Check

No GIS/PDF/generated artifact, private path, actual operational coordinate,
credential, external-device instruction, or autopilot content is committed.

## Follow-up Tasks

Implement and test the separate future runtime after contract review; then collect
local adapter smoke and separately review field-validation and human-report limits.
