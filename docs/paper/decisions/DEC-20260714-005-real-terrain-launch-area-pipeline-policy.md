# DEC-20260714-005 - Real-Terrain Launch-Area Pipeline Policy

## Decision

Task 035B will implement a first real-terrain pipeline that ends at:

```text
production-neutral candidate analysis records
+ rendering-independent candidate map features
+ deterministic summary and warnings
```

It will not include map rendering, route search, waypoints, minimum-altitude integration, UI, or field validation.

## Context

The repository already contains individually tested components for a local GeoTIFF adapter, adapter-backed terrain profiles, DSM LOS, DSM Fresnel and dominant-obstacle diagnostics, scoring, color classification, source-zone interpretation, and rendering-independent outputs. The components are not yet connected into an actual DEM/DSM candidate-grid analysis pipeline.

The current synthetic end-to-end path cannot be used as the real runtime boundary because:

- `SyntheticCandidateRecord` is explicitly synthetic;
- the synthetic record lacks real projected geometry and terrain failure states;
- `build_candidate_cell_map_features(...)` creates placeholder geometry;
- source-zone defaults can incorrectly imply ESA-derived coverage;
- current GeoTIFF value methods repeatedly validate and reopen rasters.

## Alternatives

### A. Candidate records only

- lowest implementation risk;
- good pure-test boundary;
- does not complete the map-renderer handoff needed for visible product progress.

### B. Candidate records and rendering-independent features

- keeps GIS access inside the analysis engine;
- provides actual projected geometry without rendering;
- supports deterministic tests and future renderer work;
- isolates route and UI failures from terrain analysis.

### C. Candidate, route, and waypoint integration

- crosses several currently synthetic-specific boundaries at once;
- makes failures difficult to isolate;
- expands performance and testing scope beyond the first real-terrain milestone.

### D. Rendered map integration

- adds external map/UI dependencies and visual verification;
- cannot be adequately verified in normal CI;
- couples core terrain correctness to presentation work.

## Selected Pipeline Scope

Alternative B is selected.

Public module:

```text
src/uav_rf_terrain/real_terrain_candidate_analysis.py
```

Public function:

```python
analyze_real_terrain_launch_area(
    adapter,
    config,
    *,
    source_zone_provider=None,
)
```

## Coordinate Decision

Task 035B starts with projected `LocalPoint` input in `EPSG:5179`.

MGRS remains the project default user-facing coordinate, but the MGRS-to-WGS84-to-EPSG:5179 wrapper and candidate-to-MGRS output conversion are deferred. This avoids making the first real-terrain pipeline dependent on optional projection packages and permits pure CI tests.

Internal feature x/y values are renderer geometry. They are not default user-facing coordinate fields.

Real GeoTIFF point sampling uses the open raster affine transform with lower bounds inclusive and upper bounds exclusive. The current metadata-rounding helper is not the authoritative real-GeoTIFF point sampler.

## Altitude Decision

```text
launch ground = candidate DEM MSL
launch antenna MSL = candidate DEM MSL + configurable antenna AGL
target flight MSL = target DEM MSL + allowed AGL
DSM = obstruction surface
```

The master-plan ground assumption is represented by `launch_antenna_height_agl_m=0.0` as the configuration default.

Because the existing LOS analyzer includes endpoints and treats equality as blocked, Task 035B adds a real-pipeline-only occupied-endpoint policy. Candidate and target endpoint surface validity is checked first, and only interior samples trigger the strict LOS cap. The standalone LOS API and regression behavior remain unchanged.

## Record Decision

Introduce a new frozen production-neutral `CandidateAnalysisRecord` rather than renaming or generalizing `SyntheticCandidateRecord`.

Reasons:

- preserves synthetic API compatibility;
- prevents synthetic naming from leaking into real runtime;
- permits explicit exclusion states and actual geometry;
- avoids forcing route and waypoint migrations into Task 035B.

## Feature Decision

Introduce `CandidateAnalysisMapFeature` in the new real-terrain module. Do not use the synthetic placeholder builder.

The feature contains actual internal `EPSG:5179` geometry, score/color data when available, exclusion state, optional source-zone metadata, and dominant-obstacle diagnostics. It remains rendering-independent.

## Candidate State Decision

Exact states:

```text
valid_scored
outside_operating_radius
outside_raster_extent
terrain_nodata
launch_surface_obstructed
coincident_with_target
profile_unavailable
analysis_invalid
```

Only `valid_scored` records have scores and non-excluded colors. Data failures and bounds conditions are never represented as score zero.

A valid LOS-blocked candidate is still `valid_scored`; the existing strict LOS cap produces shielding score zero and color classification handles the result.

## Fatal and Partial Result Decision

Dataset/config/target failures are fatal. Candidate-local bounds, NoData, profile, and domain-analysis failures become explicit excluded records.

Partial results are allowed, including a result with zero valid scored candidates. A zero-valid result contains the full deterministic exclusion distribution and the warning:

```text
no valid scored candidates were produced
```

## Source-Zone Decision

Source-zone integration is optional and batch-oriented.

```text
available
not_requested
unavailable
not_applicable
```

Missing or failed source-zone data does not invalidate DEM/DSM scores and is never defaulted to ESA-derived. Source-zone metadata does not change scoring, color, ordering, or candidate state.

## Performance Decision

Task 035B must provide an analysis-session path that validates metadata once and keeps one DEM and one DSM handle open for the analysis. Full-raster preload is not required.

Default guards:

```text
max candidate count: 2,500
max profile samples per candidate: 512
max total profile samples: 250,000
```

First local smoke:

```text
radius <= 900m
candidate spacing >= 180m
profile spacing >= 90m
candidate square <= 121 cells
profile samples <= 11 per valid candidate
```

## Compatibility Boundary

Unchanged:

```text
dsm_fresnel_score == average_fresnel_score
DSM LOS 0.40 + DSM Fresnel 0.60
shielding 0.80 + distance 0.20
strict LOS cap
color thresholds
candidate ranking behavior
route cost
waypoint cost
preview/report/CLI contracts
synthetic scenario and placeholder map-builder regressions
```

## Paper Boundary

The Task 035B output may support later tables showing state/color/source-zone counts and synthetic-versus-local pipeline behavior. It is not measured RF evidence, full link-budget validation, terrain-accuracy validation, communication-success evidence, reconnaissance-success evidence, or flight-feasibility evidence.

## Product and Deployment Boundary

No renderer, web application, Android/TMMR packaging, external-device integration, autopilot function, or flight-control output is authorized.

## Public Repository Sensitivity Check

This decision contains only public code contracts and aggregate guardrails. It contains no private local path, actual coordinate, credential, GIS raster, `METADATA_MAP` content, generated artifact, operational command, or device-control content.

## Follow-Up Task

Task 035B may implement the approved engine, session, pure tests, and optional bounded local smoke. Task 035B must keep actual DEM/DSM and generated output outside Git and must report any required contract expansion before modifying protected modules.
