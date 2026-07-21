# Task 036A Handoff - Real-Terrain Minimum-Altitude Contract

## Current Task

Task 036A is an approved contract and audit for future real-terrain minimum-required
MSL and AGL proxy analysis. It creates no runtime implementation.

## Current Branch / Draft PR

merged PR #109; merge commit `f3a0758`.

## Proposed Contract

- Consume a complete `RealTerrainRouteResult`, authoritative
  `SelectedLaunchSiteRecord`, one exact-parity `TerrainDataAdapter` session, and a
  MGRS converter.
- The selected record's projected point is the actual radial-profile origin.
  `route_result.launch_ground_msl_m` is DEM at that actual point, not snapped-node
  ground. The profile to the first snapped route sample evaluates the connector.
- Require selected candidate/MGRS/conversion parity and, after the sole session opens
  but before its first terrain call, exact session metadata parity with
  `route_result.terrain_metadata`.
- Keep reviewed `source_total_distance_3d_m` distinct from resampling, guard, tie,
  and radial `_2d_m` distances.
- Return comparison-only constant-route MSL per available source route. Separately
  evaluate current fixed AGL at every route sample, retaining minimum margin, meets
  proxy boolean, and a deficit-limiting sample independent of constant-MSL limiting.
- AGL over highest route DEM and target DEM is nonnegative by contract; no negative
  clamp or warning exists.

## Terrain-Session Sequence

1. Without terrain access, validate route result, selected record, config, frequency,
   resource inputs, public-safe label, and MGRS authority.
2. Open exactly one terrain session.
3. Before its first `sample_point` or `extract_profile`, require exact-policy
   `session.metadata == route_result.terrain_metadata`.
4. Sample the actual selected launch point; DEM must match
   `route_result.launch_ground_msl_m` within tolerance.
5. From that same selected-point sample, require DSM not to exceed launch antenna MSL.
6. Run route 2D sample and aggregate radial-profile resource preflight from that
   actual selected point.
7. Only then begin route `sample_point` and radial `extract_profile` calls.

Metadata mismatch, selected-point DEM mismatch, or launch DSM occupancy failure is
fatal before profile extraction and returns no partial result.

## Decision Governance

DEC-009 is `Approved by GPT Master` after exact-head CI #899 succeeded and review
threads were resolved.

## Legacy Compatibility

`src/uav_rf_terrain/minimum_altitude.py` remains the Task 015 synthetic single-profile
API. No source, test, workflow, dependency, or GIS change is part of Task 036A.

## Verification

The required local commands are regression checks because source and tests remain
unchanged. Exact final-head CI is recorded in the Draft PR completion comment and
completion report under the non-recursive ledger policy.

## Paper and Safety Boundary

This is an offline DSM/LOS/Fresnel clearance proxy proposal. It is not obstacle
clearance certification, flight-safety approval, communication-success evidence,
regulatory approval, airspace authorization, or autopilot output.

## Next Implementation Task

Implement the separate runtime module. Required coverage
includes selected-launch authority, exact terrain metadata parity, 2D/3D distances,
profile provenance and guards, MSL inversion, all-sample baseline margins, nonnegative
AGL, warning order, MGRS output, and public-coordinate omission.
