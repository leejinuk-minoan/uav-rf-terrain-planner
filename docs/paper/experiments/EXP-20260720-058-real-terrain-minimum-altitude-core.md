# EXP-20260720-058 - Real-Terrain Minimum-Altitude Pure Core

## Date

2026-07-21

## Related Task / Issue / PR

Task 036B, Issue #110, Draft PR #111, branch
`agent/task-036b-real-terrain-minimum-altitude-core`.

## Input Data

Synthetic immutable `RealTerrainRouteResult`, `SelectedLaunchSiteRecord`, prepared
route samples, and `TerrainProfile` fixtures only. No GIS raster, terrain session,
private path, or operational coordinate is used.

## Scenario / Configuration

Tests use reviewed source route modes, actual selected-launch authority, 2D route
and radial distances, 3D source totals, 300 MHz synthetic frequency, fixed 20 m AGL,
and the configured Fresnel clearance-ratio proxy. Ratio, spacing, tolerance, profile,
source-authority, and mutation boundaries are checked independently.

## Method

The pure engine accepts exact route and selected-launch contracts, reruns their
validators, validates prepared geometry/profile parity before Fresnel work, then
computes the approved inversion and separate all-sample current fixed-AGL margins.
Recursive output validation recomputes formula and limiter parity while public output
keeps MGRS-facing status and omits projected points, profiles, raster details, and
metadata internals.

## Expected Result

- Duck-typed or directly mutated source authority is fatal.
- Prepared 2D/radial/profile endpoint and spacing mismatches are fatal before Fresnel
  calculation.
- Tolerance-aware limiter selection is deterministic.
- Output revalidation rejects direct or coordinated nested formula/authority mutation.
- No partial result, terrain session, GIS access, route ranking change, or operational
  claim is produced.

## Actual Result

The local amendment passed focused source/selection/prepared-evidence/output contract
tests (`70 passed`), relevant Task 035EF/035G plus legacy regression tests (`58
passed`), and the full suite (`983 passed, 1 skipped`). It retains private exact
source and prepared-profile authority for recursive validation, rejects collection
substitution and non-finite geometry, and keeps that authority out of public output.
The amendment remains local-only pending final local commit and review.

## Metrics

- Focused categories: source authority, profile geometry, resource guard ordering,
  typed error mapping, tolerance tie, recursive output formula, public omission, and
  one/two/three route parity.
- Regression categories: legacy minimum-altitude and complete project test suite.

## Local / CI Evidence

Fresh local verification recorded `70` focused tests, `58` related regression tests,
and `983 passed, 1 skipped` for the full suite. Exact final-head GitHub Actions
evidence remains pending under the non-recursive policy: it belongs in the Draft PR
completion comment after the local final head is published, and does not justify a
CI-only follow-up commit.

## Interpretation

This is an offline DSM/LOS/Fresnel clearance proxy calculation core. It does not
demonstrate obstacle absence, communication success, flight feasibility,
reconnaissance success, approval, authorization, or field performance.

## Limitations

Task 036B deliberately excludes `TerrainDataAdapter` session orchestration,
`sample_point`, `extract_profile`, raster loading, real GIS smoke validation, UI,
route selection, device control, and autopilot behavior. Those boundaries remain for
reviewed future work.

## Paper Figure / Table Candidate

Candidate table: source authority, prepared-evidence geometry, inversion inputs,
constant-MSL limiter, current-margin limiter, and public-output omission matrix.

## Sensitivity / Adversarial Cases

Direct frozen-dataclass mutation, coordinated source/result mutation, fake sources,
wrong route totals, wrong radial distance, reversed or unrelated profiles, spacing and
endpoint terrain mismatch, zero/coincident occupancy, resource guards before Fresnel,
and tolerance-boundary ties are test targets.

## Public Repository Sensitivity

No raster, generated artifact, private local path, credential, actual operational
coordinate, external-device instruction, or flight-control data is recorded.

## Follow-ups

1. Complete final local verification and Codex Master review.
2. Publish one approved final local head only after local review.
3. Perform exact-head CI and external audit while PR #111 remains Draft.
4. Start Task 036C only after the approved Task 036B merge lifecycle is complete.
