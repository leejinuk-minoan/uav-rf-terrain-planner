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
metadata internals. Numeric result fields retain exact finite global max/min values;
limiter IDs use deterministic representatives within the configured absolute tolerance
band and are reported with that provenance policy.

## Expected Result

- Duck-typed or directly mutated source authority is fatal.
- Prepared 2D/radial/profile endpoint and spacing mismatches are fatal before Fresnel
  calculation.
- Exact numeric extremes and tolerance-aware canonical limiter selection are both
  deterministic and independently validated.
- Output revalidation rejects direct or coordinated nested formula/authority mutation.
- No partial result, terrain session, GIS access, route ranking change, or operational
  claim is produced.

## Actual Result

The fifth local amendment passed focused source/selection/prepared-evidence/output
contract tests (`128 passed`), relevant Task 035EF/035G plus legacy regression tests
(`58 passed`), and the full suite (`1041 passed, 1 skipped`). It retains one compact
canonical authority snapshot plus an independent canonical emitted-output fingerprint.
The seals cover retained calculation authority and every emitted nested output field;
recursive validation checks them before tolerance-aware mathematical replay. It also
reruns exact terrain metadata validation, rejects collection substitution/non-finite
geometry/profile ordering errors, and keeps private evidence out of public output.
The final amendment also shares generic selection logic between the engine and output
validator, emits exact global numeric extremes separately from canonical limiter IDs,
and records `distance_tolerance_m` plus limiter semantics in public output. Local
verification for this document content is complete.

## Metrics

- Focused categories: source authority, exact metadata, profile geometry, resource
  guard ordering, typed error mapping, canonical authority/output fingerprints,
  exact-extreme/tolerance-representative replay and ties, recursive output formula,
  public provenance omission, and one/two/three route parity.
- Regression categories: legacy minimum-altitude and complete project test suite.

## Local / CI Evidence

Fresh local verification recorded `128` focused tests, `58` related regression tests,
and `1041 passed, 1 skipped` for the full suite. Exact final-head GitHub Actions
evidence remains pending under the non-recursive policy: it belongs in the external
completion report after the local final head is published, and does not justify a
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

Direct frozen-dataclass mutation, coordinated source/result mutation, sub-tolerance
public-output mutation, fake sources, exact nested metadata mutation, wrong route
totals, wrong radial distance, reversed or unrelated profiles, spacing and endpoint
terrain mismatch, sub-tolerance XY coincidence, resource guards before Fresnel, exact
global-extreme versus canonical-limiter identity, and tolerance-boundary ties are test
targets.

## Public Repository Sensitivity

No raster, generated artifact, private local path, credential, actual operational
coordinate, external-device instruction, or flight-control data is recorded.

## Follow-ups

1. Complete final local verification and Codex Master review.
2. Publish one approved final local head only after local review.
3. Perform exact-head CI and external audit while PR #111 remains Draft.
4. Start Task 036C only after the approved Task 036B merge lifecycle is complete.
