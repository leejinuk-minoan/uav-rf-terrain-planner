# EXP-20260716-056 - Real-Terrain Waypoint Reporting

## Date

2026-07-16

## Related Task/Issue/PR

Task 035G; Issue #106; Draft PR #107.

## Experiment Purpose

Verify deterministic MGRS-facing waypoint reporting over a complete Task 035EF route
result without terrain, LOS/Fresnel, score, color, graph, or route recomputation.

## Input Data

Synthetic in-memory immutable `RealTerrainRouteResult` fixtures with complete graph,
route candidate, handoff, MGRS, snap, and `NOT_REQUESTED` source-zone metadata. No
local GIS raster, actual coordinate, generated report, browser, or field input is
used.

## Scenario/Configuration

The default configuration uses 500 m spacing, fixed five-digit MGRS precision,
deterministic start/end inclusion, a bounded per-route/total waypoint count, and
strict distance tolerance. Coverage includes 3/2/1 route sets, all start/end policy
combinations, short and zero-distance routes, exact nodes, and interior interpolation.

## Method

1. Revalidate the complete route result before report construction.
2. Derive cumulative 3D sampling targets before any coordinate conversion and apply
   the count guards before invoking the MGRS converter.
3. Reuse exact handoff values; for strict interior samples, linearly interpolate
   elevations and retain conservative color and score values.
4. Retain minimum private route/snap/launch-ground authority in the result and verify
   report, summary, warning, total-distance, endpoint, and height-difference parity.
5. Convert each unique waypoint projected point through an in-memory MGRS cache and
   assert public output excludes projected/private authority fields.

## Expected Result

Reports retain source route order, approximate fixed spacing, configured endpoint
policy, fixed AGL, deterministic warnings, and `NOT_REQUESTED` source-zone metadata.
Malformed input, conversion failure, and guard failures must produce typed failures
before partial output.

## Actual Result

Focused synthetic tests cover exact/interior records, strict interpolation fractions,
short/endpoint-only/zero-distance warning parity, all endpoint combinations,
authority mutation rejection, public-output boundaries, MGRS error mapping,
guard-before-conversion, and forward-only sampling cursor behavior. Results are
deterministic reporting proxies over existing route handoffs.

## Metrics

The review-amendment focused suite contains 22 tests across reporting and output
contracts; the fresh full suite contains 914 tests. The exact final PR-head hosted CI
evidence belongs in the PR completion/review comment and the completion report, then
in the next post-merge ledger reconciliation.

## CI/Local Test Result

Initial Draft evidence before the review amendment: reporting 5 + outputs 2 focused
tests, 899 full tests, and CI #888 / run 29471833777 success for head
`8ac72857688ebdf0dbb29f810df2c53a81cd7baa`. The review-amendment local focused 22,
full 914, `compileall`, Ruff, mypy, and diff checks passed. Exact final-head CI is
pending at this record revision.

## Interpretation

The evidence supports deterministic software-contract behavior for waypoint report
construction. It does not validate route quality, actual obstacle absence, RF link
availability, flight feasibility, reconnaissance success, or airspace approval.

## Limitations

Fixtures are synthetic and use fake coordinate conversion. No GIS-backed route smoke,
browser/UI verification, waypoint usability study, field RF measurement, or flight
test is included. Source-zone metadata remains `NOT_REQUESTED` by MVP policy.

## Paper Figure/Table Candidate

A methods table can compare exact-node reuse and strict interior interpolation,
including distance target, elevation semantics, conservative score/color semantics,
warning policy, and source-zone state. This is an implementation-contract figure, not
an operational performance result.

## Public Repo Sensitivity

No GIS raster, generated artifact, private path, actual operational coordinate,
credential, external-device instruction, or flight-control file is committed.

## Follow-up

After PR #107 merges, reconcile final head, merge commit, Issue closure, final local
test count, and exact hosted CI in `RESEARCH_BUILD_RECORD.md` during the next Task.
Future work may separately study waypoint-report usability, GIS-backed smoke tests,
and field RF validation.
