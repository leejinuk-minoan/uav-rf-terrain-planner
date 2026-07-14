# EXP-20260714-051 - Real-Terrain Launch-Area Contract Audit

## Experiment Purpose

Audit the current terrain, GeoTIFF, profile, LOS/Fresnel, scoring/classification, source-zone, synthetic-output, and map-output code contracts and define a bounded first real-terrain candidate-analysis implementation contract.

This record is a **code/document audit**. It is not a runtime experiment, local GIS validation, RF validation, or field test.

## Inputs Reviewed

Repository source and tests only:

```text
coordinate structures and distance helpers
candidate grid generation
terrain adapter metadata and alignment validation
local GeoTIFF adapter
adapter-backed terrain profile extraction
DSM LOS and strict cap
DSM Fresnel and dominant-obstacle diagnostics
candidate scoring and color classification
source-zone enum, raster classifier, and candidate assignment scaffold
synthetic candidate/scenario records
rendering-independent map output records
candidate display/preview boundaries
existing pure and fake-raster tests
historical local DEM/DSM and QGIS handoffs
```

No GeoTIFF, DEM, DSM, landcover raster, QGIS project, `METADATA_MAP` file, or generated output was opened by Task 035A.

## Audit Method

1. Verify Task 034D merge and Issue completion on GitHub.
2. Read the actual current APIs and their tests.
3. Trace the proposed real path from projected target to candidate feature.
4. Identify type, coordinate, altitude, failure, and performance gaps.
5. Compare candidate-only, candidate-plus-feature, route-inclusive, and rendered-map scopes.
6. Define one exact Task 035B contract and protected boundaries.

## Current-State Findings

### Reusable components

- deterministic candidate IDs and grid order;
- DEM/DSM metadata alignment validation;
- explicit NoData and bounds errors;
- adapter-backed profile sampling;
- DSM LOS and Fresnel analysis;
- dominant-obstacle diagnostic projection;
- existing score weights, strict LOS cap, and color thresholds;
- batch local source-zone raster sampling;
- rendering-independent style metadata.

### Structural gaps

- no actual target-to-candidate real-terrain orchestration;
- generic metadata point conversion uses rounding rather than the real raster affine transform;
- GeoTIFF cell reads repeatedly validate and reopen rasters;
- adapter profiles request DEM, DSM, and delta separately for each sample;
- grid `distance_3d_m` is not terrain-authoritative before altitude resolution;
- standalone LOS counts occupied endpoints as blocked when DSM equals endpoint line height;
- `SyntheticCandidateRecord` lacks actual geometry and exclusion states;
- current candidate feature builder creates placeholder coordinates;
- existing source-zone assignment is per-point, fatal-on-provider-error, and has no unavailable state.

### Raster-edge contract correction

The Task 035B contract supports only north-up GeoTIFF transforms where `a > 0`, `e < 0`, `b == 0`, and `d == 0`. The authoritative point-to-cell operation is `dataset.index(x, y)`, followed by `0 <= row < height` and `0 <= col < width`. A directional precheck is secondary and uses `left <= x < right` and `bottom < y <= top`: left and top are inclusive, while right and bottom are exclusive. Other transform signs, rotation, or shear are fatal `RealTerrainLaunchAreaAnalysisError` conditions.

## Alternatives Evaluated

| Scope | Result |
|---|---|
| Candidate records only | testable but incomplete renderer handoff |
| Candidate records plus rendering-independent features | selected |
| Candidate plus route/waypoint | deferred because of broad synthetic migration and failure coupling |
| Rendered map | deferred because of UI/GIS dependency and manual visual verification scope |

Coordinate alternatives:

| Input | Result |
|---|---|
| MGRS from first implementation | deferred; optional conversion/projection dependency is incomplete |
| EPSG:5179 `LocalPoint` | selected for Task 035B |
| Both in one config | rejected as ambiguous and over-broad |

Record alternatives:

| Model | Result |
|---|---|
| Rename/generalize `SyntheticCandidateRecord` | rejected due regression and name mismatch |
| New production-neutral record | selected |
| Real adapter only around existing placeholder builder | rejected because required state/geometry fields are missing |

Source-zone alternatives:

| Policy | Result |
|---|---|
| mandatory | rejected because landcover availability would block core terrain analysis |
| optional batch provider | selected |
| completely deferred | rejected because current local source sensitivity is material and a clean optional hook already exists |

## Selected Contract Summary

```text
module: real_terrain_candidate_analysis.py
input: EPSG:5179 LocalPoint + frozen config + terrain adapter
output: frozen candidate records + actual projected map features + summary + warnings
source zone: optional batch provider
route/waypoint/map rendering: excluded
```

Altitude:

```text
launch ground MSL = candidate DEM
launch antenna MSL = candidate DEM + configured antenna AGL
target flight MSL = target DEM + allowed AGL
DSM = obstruction surface
```

The default launch antenna AGL is zero to preserve the master-plan assumption, but occupied endpoints are not counted as intervening LOS blockers. A candidate whose DSM exceeds the antenna MSL is explicitly excluded.

## Fatal-versus-Exclusion Result

Fatal:

```text
invalid configuration
dataset metadata mismatch
non-EPSG:5179 dataset
target outside raster
target NoData/non-finite
target surface above target flight altitude
session creation failure
performance guard violation
unexpected implementation exception
```

Candidate-level exclusion:

```text
outside operating radius
outside raster extent
candidate NoData/non-finite
launch surface above antenna
coincident target/profile unsupported
profile NoData/unavailable
candidate-specific domain analysis invalid
```

Source-zone failure produces an unavailable metadata state and warning without changing the core candidate score.

Source-zone provider eligibility requires `sampled_cell_center is not None` and excludes `outside_operating_radius`, `outside_raster_extent`, and `terrain_nodata`. The eligible provider batch preserves filtered input candidate order and requires an equal-length, same-order response. `valid_scored`, `launch_surface_obstructed`, `coincident_with_target`, `profile_unavailable`, and `analysis_invalid` use `not_requested` when omitted, `available` when successful, and `unavailable` when the provider fails. The three excluded states use `not_applicable` in all provider cases. A provider failure leaves eligible core state and score unchanged and produces one deterministic warning.

## Performance Audit Result

The current local adapter method pattern is unsuitable for a candidate grid because it can reopen DEM/DSM several times per profile sample. Task 035B must introduce a one-session access path:

```text
one metadata validation
one DEM open
one DSM open
session-reused point/profile reads
optional one source-zone batch session
```

Default safety limits were set to 2,500 candidates, 512 profile samples per candidate, and 250,000 total profile samples. The first optional local smoke is bounded to a 900m radius, 180m candidate spacing, and 90m profile spacing.

## Test Contract Result

Task 035B pure CI tests must cover:

```text
flat/ridge/building synthetic adapters
frequency changes
2D/3D radius boundaries
raster edge and NoData behavior
exact left/right/top/bottom edges with inside/outside epsilons
unsupported transform signs, rotation, and shear fatal behavior
target fatal versus candidate exclusion
endpoint occupancy policy
strict LOS and exact scoring/color regression
dominant diagnostics
source-zone membership, input order, response count, and omitted/success/failure availability for every candidate state
actual feature geometry and placeholder exclusion
input immutability and deterministic ordering
session open-count behavior
existing synthetic/preview/report/CLI regressions
```

Local integration and QGIS checks remain optional, bounded, user-data-dependent, and non-committing.

## Actual Result

The architecture boundary, decision record, Task 035B handoff, and project current-state notes were prepared. No runtime implementation or local GIS result was produced.

## Metrics

Audit metrics:

```text
pipeline alternatives compared: 4
coordinate alternatives compared: 3
record alternatives compared: 3
source-zone alternatives compared: 3
selected runtime end point: candidate records + rendering-independent features
runtime source changed by Task 035A: 0
runtime tests changed by Task 035A: 0
GIS files accessed by Task 035A: 0
```

## Interpretation

The repository has sufficient pure analysis components to begin a real-terrain candidate pipeline, but not by directly joining the current synthetic scenario and placeholder map builder. The selected contract isolates a first useful real-data milestone while preserving existing score, route, output, and UI contracts.

## Limitations

- Task 035A did not execute rasterio, GDAL, QGIS, GeoTIFF sampling, or candidate analysis.
- Historical local checks cover selected data and proxy rasters, not nationwide terrain accuracy.
- The temporary DSM remains a landcover-derived proxy, not measured building/canopy height.
- Mixed ESA/WMS/fallback zones can materially affect surface-delta interpretation.
- The contract does not validate communication performance or flight feasibility.

## Figure/Table Candidacy

Future Task 035B results may support:

- candidate state-count table;
- color-count table;
- source-zone availability/stratification table;
- synthetic-versus-local contract diagram;
- bounded QGIS overlay figure after separate sanitization approval.

No figure, table artifact, or raster output is committed by Task 035A.

## Public Repository Sensitivity Check

Only repository-relative source names, public contract fields, aggregate historical raster characteristics, and non-operational guardrails are recorded. No private path, actual candidate coordinate, credential, GIS file, generated output, device command, autopilot command, or flight-control content is included.
