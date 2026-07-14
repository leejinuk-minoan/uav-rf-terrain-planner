# Real-Terrain Launch-Area Analysis Pipeline Boundary

## Purpose

This document defines the reviewed Task 035B contract for connecting the existing terrain, LOS/Fresnel, scoring, classification, source-zone, and rendering-independent output components to a first real-terrain launch-area candidate analysis pipeline.

Task 035A is a documentation and code-contract audit only. It does not execute GeoTIFFs, access `METADATA_MAP`, change runtime source or tests, render maps, implement routes or waypoints, or validate RF or flight outcomes.

## Verified Baseline

```text
PR #95: merged to main
PR #95 merge commit / base main SHA: 66f2eb7982bea47598b13afd7fffe157fcdbfcb6
Issue #94: closed / completed
Issue #96: open
Task 034D implementation and EXP-20260714-050: present on main
open PRs before Task 035A: none
```

## Current Component Audit

### Coordinate structures

`coordinates.py` provides frozen `LocalPoint`, WGS84 placeholders, 2D/3D distance helpers, and an optional MGRS-to-WGS84 helper. It does not provide the complete MGRS-to-EPSG:5179 projection path needed for a production user-input wrapper.

### Candidate grid

`grid.py` provides deterministic square-window candidate generation. Iteration is ordered by increasing `ix`, then increasing `iy`, and IDs are stable:

```text
cell_x{ix:+04d}_y{iy:+04d}
```

The current `CandidateCell.distance_3d_m` is calculated from the input `LocalPoint.z_m` values. It is not authoritative for real-terrain analysis before candidate and target elevations are sampled.

### Terrain adapter and GeoTIFF adapter

`TerrainDataAdapter` exposes metadata validation and index-based DEM/DSM reads. `LocalGeoTiffTerrainDataAdapter` validates alignment, CRS, square pixels, bounds, dimensions, NoData, and finite values.

The current GeoTIFF adapter is correct as a small adapter smoke boundary but is not an acceptable high-volume candidate pipeline access pattern:

- every DEM or DSM value request validates metadata again;
- metadata validation opens both rasters;
- each value request reopens its raster;
- `get_surface_delta_m()` repeats DSM and DEM access;
- adapter-backed profile extraction requests DEM, DSM, and delta separately for every sample.

Task 035B must not perform candidate-by-candidate and sample-by-sample file reopening.

### Projected point to raster cell

The current generic metadata helper converts a point to an index by rounding from metadata bounds. Real GeoTIFF point sampling must instead use the open raster affine transform or equivalent `dataset.index(x, y)` semantics.

Task 035B real-GeoTIFF rules are:

```text
left / bottom bound: inclusive
right / top bound: exclusive
point-to-cell: open-raster affine transform
candidate geometry: requested projected point
sample cell: raster cell containing that point
```

The metadata-rounding helper remains valid for current synthetic/in-memory tests but is not the authoritative real-GeoTIFF point sampler.

### Terrain profile

`extract_terrain_profile_from_adapter(...)` includes start and end samples, uses deterministic straight-line fractions, permits duplicate sampled indices, and raises explicit profile errors. Its storage-independent contract is reusable, but its current per-sample adapter calls require a session-backed replacement or wrapper for real GeoTIFF scale.

### LOS and endpoint semantics

`analyze_dsm_los(...)` marks a sample blocked when:

```text
dsm_msl >= los_line_msl
```

It includes start and end samples in that rule. Therefore a launch antenna exactly at DEM/DSM surface elevation would be marked blocked at its own endpoint.

For the real-terrain pipeline, endpoints are occupied transmitter/receiver locations rather than intervening obstacles. Task 035B must preserve the existing `analyze_dsm_los(...)` API and tests, while adding a pipeline-only endpoint policy:

1. validate the candidate and target endpoint surface heights before profile analysis;
2. reject a launch candidate when `launch_dsm_msl > launch_antenna_msl`;
3. reject the entire run when `target_dsm_msl > target_flight_msl`;
4. after base LOS calculation, do not count the first and last profile samples as intervening blockers;
5. apply the strict LOS cap to interior samples only;
6. retain endpoint samples, line heights, and clearances for deterministic profile/Fresnel continuity.

Equality at an occupied endpoint is permitted. Existing standalone LOS behavior remains unchanged.

### Fresnel and diagnostics

The current Fresnel implementation is reusable without formula changes:

```text
dsm_fresnel_score == average_fresnel_score
```

Dominant-obstacle eligibility is already restricted to interior samples with positive `d1`, `d2`, and Fresnel radius. The existing `CandidateFresnelDiagnostics` projection and ten-field contract are reused.

### Scoring and classification

The existing score and color functions are reused exactly. No real-terrain-specific weights or thresholds are introduced.

### Source-zone metadata

The current local source-zone classifier supports batch point sampling with one open session across DEM, original landcover, and gap-filled landcover rasters. The existing generic candidate assignment scaffold, however, calls a provider once per cell and treats any provider failure as fatal. It also has no unavailable state.

Source-zone data must therefore be optional in Task 035B and integrated through a new batch provider boundary. Missing source-zone rasters must not block DEM/DSM candidate analysis and must never be represented as ESA-derived.

### Synthetic and map-output boundaries

`SyntheticCandidateRecord` is explicitly synthetic and lacks real geometry, terrain state, and candidate-level exclusion states. It must not become the public real-terrain record.

`build_candidate_cell_map_features(...)` accepts synthetic records and generates placeholder geometry:

```text
x_m = index * 500.0
y_m = 0.0
```

That builder and its regression behavior remain unchanged. Task 035B must not use it for real-terrain output.

## Pipeline Scope Alternatives

| Alternative | Implementation risk | Testability | GIS coupling | Evidence value | Failure isolation | Decision |
|---|---:|---:|---:|---:|---:|---|
| A. Candidate records only | low | high | moderate | partial | high | Rejected as too incomplete for renderer handoff |
| B. Candidate records plus rendering-independent candidate features | moderate | high | bounded to adapter/session | high | high | **Selected** |
| C. Candidate plus route and waypoint | high | medium | broad | mixed | low | Rejected |
| D. Rendered map | highest | low in CI | high | visually useful but premature | lowest | Rejected |

## Selected Task 035B Start and End

```text
projected target + configuration + terrain adapter
→ validated terrain analysis session
→ deterministic candidate grid
→ candidate-level DEM/DSM/profile/LOS/Fresnel/score/color analysis
→ optional batch source-zone attachment
→ production-neutral candidate records
→ rendering-independent candidate map features
→ deterministic result summary and warnings
```

Task 035B does not implement:

```text
MGRS conversion wrapper
rendered Folium/MapLibre/Streamlit map
map click selection
route search or route alternatives
waypoint generation
minimum-required-altitude integration
Android/TMMR packaging
field RF validation
```

## Public Module and Function

Create a new module:

```text
src/uav_rf_terrain/real_terrain_candidate_analysis.py
```

Do not place real runtime behavior in `scenario_outputs.py`.

Public function:

```python
def analyze_real_terrain_launch_area(
    adapter: TerrainDataAdapter,
    config: RealTerrainLaunchAreaConfig,
    *,
    source_zone_provider: SourceZoneBatchProvider | None = None,
) -> RealTerrainLaunchAreaResult:
    ...
```

The function does not mutate `adapter`, `config`, candidate input values, or provider input sequences. It performs no file output and no rendering.

## Configuration Contract

```python
@dataclass(frozen=True)
class RealTerrainLaunchAreaConfig:
    scenario_name: str
    target_point: LocalPoint
    operating_radius_m: float
    candidate_spacing_m: float
    allowed_agl_m: float
    frequency_hz: float
    profile_sample_spacing_m: float | None = None
    launch_antenna_height_agl_m: float = 0.0
    include_center: bool = False
    include_out_of_radius: bool = True
    max_candidate_count: int = 2_500
    max_profile_samples_per_candidate: int = 512
    max_total_profile_samples: int = 250_000
```

Validation:

| Field | Unit/type | Contract |
|---|---|---|
| `scenario_name` | non-empty `str` | public-safe label; no private path |
| `target_point` | `LocalPoint` | finite x/y; `z_m` must equal `0.0` because altitude is configured separately |
| `operating_radius_m` | m | positive finite |
| `candidate_spacing_m` | m | positive finite and not greater than radius |
| `allowed_agl_m` | m above DEM | positive finite |
| `frequency_hz` | Hz | positive finite |
| `profile_sample_spacing_m` | m or `None` | positive finite; `None` resolves to DEM resolution |
| `launch_antenna_height_agl_m` | m above candidate DEM | finite and non-negative; default `0.0` preserves the master-plan ground assumption |
| `include_center` | bool | default false because coincident start/end has no horizontal RF path |
| `include_out_of_radius` | bool | whether excluded radius cells remain in records/features |
| `max_candidate_count` | count | positive non-boolean integer |
| `max_profile_samples_per_candidate` | count | positive non-boolean integer |
| `max_total_profile_samples` | count | positive non-boolean integer |

Before raster access, estimate the square-window candidate count and worst-case profile-sample budget. Exceeding any configured guardrail is a fatal configuration error.

## Terrain Read Session Contract

Task 035B adds a session protocol without breaking the existing `TerrainDataAdapter` methods:

```python
class TerrainAnalysisSession(Protocol):
    metadata: TerrainDatasetMetadata

    def sample_point(self, point: LocalPoint) -> TerrainPointSample:
        ...

    def extract_profile(
        self,
        start: LocalPoint,
        end: LocalPoint,
        *,
        sample_spacing_m: float,
        scenario_name: str,
    ) -> TerrainProfile:
        ...
```

```python
@dataclass(frozen=True)
class TerrainPointSample:
    requested_point: LocalPoint
    cell_center_point: LocalPoint
    x_index: int
    y_index: int
    dem_msl: float
    dsm_msl: float
    surface_delta_m: float
```

A runtime-checkable optional session factory protocol may be used:

```python
class SupportsTerrainAnalysisSession(Protocol):
    def open_analysis_session(self) -> ContextManager[TerrainAnalysisSession]:
        ...
```

Behavior:

- `LocalGeoTiffTerrainDataAdapter.open_analysis_session()` opens DEM and DSM once each;
- metadata is validated once per session;
- point sampling uses the open affine transform;
- profile samples reuse the same open handles;
- rasters are closed when the context exits;
- generic/in-memory adapters may use a compatibility session wrapper over existing protocol methods for CI tests;
- Task 035B does not load complete nationwide rasters into memory.

## Coordinate Contract

### Task 035B input

Selected alternative: projected input first.

```text
target_point.x_m / y_m = EPSG:5179 meters
target_point.z_m = 0.0
```

Task 035B requires validated dataset CRS `EPSG:5179`. Other CRS values are fatal for this first pipeline.

### Deferred MGRS wrapper

MGRS remains the default user-facing project coordinate policy, but Task 035B is a developer/runtime engine boundary. A later wrapper must provide:

```text
MGRS → WGS84 → EPSG:5179 target LocalPoint
EPSG:5179 candidate point → MGRS display field
```

Task 035B does not claim MGRS input support.

### Internal coordinates

Internal projected coordinates and raster indices are allowed only in analysis/session and map-geometry records. They are not default user-facing fields.

```text
candidate feature x/y = internal renderer geometry
raster row/col or x/y index = internal sampling data
candidate_cell_mgrs = None in Task 035B
coordinate_display_state = projected_only
```

## Candidate Grid and Raster Contract

1. Generate the square candidate window around `target_point` with existing deterministic `ix`/`iy` ordering.
2. Candidate IDs remain the existing stable grid IDs.
3. Current grid `distance_3d_m` and radius flag are treated as horizontal prechecks only.
4. A candidate whose 2D distance exceeds the radius is `outside_operating_radius` without raster/profile analysis.
5. For candidates within the 2D radius, resolve the raster cell through the session transform.
6. The target point must resolve to a valid DEM/DSM cell before candidate generation results are accepted.
7. Candidate points outside the raster are candidate-level exclusions.
8. Candidate masked/NoData or non-finite DEM/DSM cells are candidate-level exclusions.
9. Do not convert bounds or NoData conditions to numeric zero.
10. The requested projected candidate point remains feature geometry; sampled cell-center geometry is retained only as internal diagnostic data.

## Altitude and Distance Semantics

```text
launch_ground_msl = candidate DEM MSL
launch_surface_msl = candidate DSM MSL
launch_antenna_msl = launch_ground_msl + launch_antenna_height_agl_m

target_ground_msl = target DEM MSL
target_surface_msl = target DSM MSL
target_flight_msl = target_ground_msl + allowed_agl_m
```

Rationale:

- AGL is referenced to DEM terrain, not the top of vegetation or a building proxy.
- DSM remains the obstruction surface for endpoint validation, LOS, and Fresnel.
- A candidate is excluded as `launch_surface_obstructed` when its DSM exceeds the configured antenna MSL.
- The run is fatal when target DSM exceeds target flight MSL because one invalid target altitude affects every candidate.
- Equality at an occupied endpoint is allowed and endpoints are not treated as intervening LOS obstacles.

Authoritative operating distance:

```text
distance_3d_m = distance between
(candidate x, candidate y, launch_antenna_msl)
and
(target x, target y, target_flight_msl)
```

A candidate can pass the horizontal precheck but fail the authoritative 3D radius check.

## Candidate Analysis States

```python
class CandidateAnalysisState(StrEnum):
    VALID_SCORED = "valid_scored"
    OUTSIDE_OPERATING_RADIUS = "outside_operating_radius"
    OUTSIDE_RASTER_EXTENT = "outside_raster_extent"
    TERRAIN_NODATA = "terrain_nodata"
    LAUNCH_SURFACE_OBSTRUCTED = "launch_surface_obstructed"
    COINCIDENT_WITH_TARGET = "coincident_with_target"
    PROFILE_UNAVAILABLE = "profile_unavailable"
    ANALYSIS_INVALID = "analysis_invalid"
```

Rules:

- Only `valid_scored` has a `CandidateScore` and non-excluded color.
- Every other state uses `ColorClass.EXCLUDED`, score fields `None`, and diagnostic fields `None`.
- Exclusion states are not score zero.
- A LOS-blocked but otherwise valid candidate remains `valid_scored`, has LOS score zero, receives the strict shielding cap, and normally classifies red. LOS blocking is an analysis result, not a data failure.

## Candidate Analysis Sequence

For each candidate in deterministic grid order:

```text
1. use already validated dataset/session metadata
2. perform 2D radius precheck
3. resolve candidate projected point to raster cell
4. read candidate DEM/DSM once through the session
5. derive launch and target endpoint MSL values
6. evaluate authoritative 3D operating distance
7. reject coincident start/end when explicitly included
8. extract the candidate-to-target terrain profile
9. calculate base DSM LOS
10. apply the occupied-endpoint LOS policy and interior strict cap
11. calculate DSM Fresnel analysis
12. project dominant-obstacle diagnostics
13. compute candidate score with existing weights
14. classify with existing color thresholds
15. create production-neutral candidate record
```

After all core candidate records are built:

```text
16. attach optional source-zone metadata in one batch
17. build rendering-independent candidate features
18. build deterministic state/color/source-zone summary
19. return warnings and result
```

## Production-Neutral Candidate Record

Selected alternative: introduce a new record; do not rename or generalize `SyntheticCandidateRecord` in Task 035B.

```python
@dataclass(frozen=True)
class CandidateAnalysisRecord:
    candidate_id: str
    candidate_point: LocalPoint
    sampled_cell_center: LocalPoint | None
    state: CandidateAnalysisState
    reason: str
    distance_2d_m: float
    distance_3d_m: float | None
    within_operation_radius: bool
    launch_ground_msl: float | None
    launch_surface_msl: float | None
    launch_antenna_msl: float | None
    profile_sample_count: int | None
    candidate_score: CandidateScore | None
    color_class: ColorClass
    fresnel_diagnostics: CandidateFresnelDiagnostics | None
    source_zone: TerrainSourceZone | None
    source_zone_state: SourceZoneAvailability
    source_sensitive: bool | None
    source_zone_reason: str
```

Full terrain profiles, LOS sample tuples, and Fresnel sample tuples are not retained in every returned record. The summary score and approved diagnostics are retained to bound memory use.

## Source-Zone Contract

```python
class SourceZoneAvailability(StrEnum):
    AVAILABLE = "available"
    NOT_REQUESTED = "not_requested"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"
```

```python
class SourceZoneBatchProvider(Protocol):
    def __call__(
        self,
        points: Sequence[LocalPoint],
    ) -> Sequence[TerrainSourceZone]:
        ...
```

Policy:

- provider is optional;
- omitted provider yields `not_requested` and no source-zone enum;
- outside-raster and terrain-NoData candidates yield `not_applicable`;
- provider is invoked once for the eligible projected point batch;
- return order and count must match input order;
- a provider exception, malformed result, or unavailable landcover raster does not invalidate DEM/DSM scores;
- affected records become `unavailable` with one result warning;
- unavailable source zones are never replaced with `ESA_DERIVED`;
- source zone never changes score, color, candidate order, or inclusion state.

A wrapper around `LocalSourceZoneRasterClassifier.sample_points(...)` is the preferred local provider because it opens its three rasters once.

## Rendering-Independent Feature Contract

Introduce a production-neutral feature in the new module rather than using the synthetic placeholder builder:

```python
@dataclass(frozen=True)
class CandidateAnalysisMapFeature:
    feature_id: str
    candidate_id: str
    x_m: float
    y_m: float
    geometry_crs: str
    candidate_cell_mgrs: str | None
    coordinate_display_state: str
    state: CandidateAnalysisState
    color_class: ColorClass
    style: MapStyle
    overall_score: float | None
    shielding_stability_score: float | None
    distance_3d_m: float | None
    within_operation_radius: bool
    reason: str
    source_zone: TerrainSourceZone | None
    source_zone_state: SourceZoneAvailability
    source_sensitive: bool | None
    source_zone_reason: str
    fresnel_diagnostics: CandidateFresnelDiagnostics | None
```

Exact Task 035B values:

```text
feature_id = candidate-feature-{zero-based grid order:05d}
x_m/y_m = actual candidate projected geometry
geometry_crs = EPSG:5179
candidate_cell_mgrs = None
coordinate_display_state = projected_only
style = style_for_color_class(color_class)
```

This is renderer input, not a rendered map and not a default user-facing coordinate record.

## Result Contract

```python
@dataclass(frozen=True)
class RealTerrainLaunchAreaResult:
    scenario_name: str
    dataset_metadata: TerrainDatasetMetadata
    target_point: LocalPoint
    target_ground_msl: float
    target_surface_msl: float
    target_flight_msl: float
    candidate_records: tuple[CandidateAnalysisRecord, ...]
    candidate_features: tuple[CandidateAnalysisMapFeature, ...]
    summary: RealTerrainLaunchAreaSummary
    warnings: tuple[str, ...]
```

```python
@dataclass(frozen=True)
class RealTerrainLaunchAreaSummary:
    total_candidate_count: int
    valid_scored_count: int
    excluded_count: int
    state_counts: tuple[tuple[str, int], ...]
    color_counts: tuple[tuple[str, int], ...]
    source_zone_state_counts: tuple[tuple[str, int], ...]
    source_sensitive_count: int
```

Ordering:

- records and features have identical length and candidate order;
- feature `candidate_id` at index N matches record `candidate_id` at index N;
- count tuples use enum declaration order, not hash-map iteration;
- warnings use deterministic pipeline-stage order.

Partial results are allowed with zero valid scored candidates. Such a result contains all available exclusion records and the exact warning:

```text
no valid scored candidates were produced
```

This is preferable to discarding the failure distribution. A caller may impose a higher product-level minimum in a later task.

## Error Contract

```python
class RealTerrainLaunchAreaAnalysisError(ValueError):
    """Fatal configuration, dataset, target, or pipeline-contract error."""
```

Fatal conditions:

| Condition | Fatal |
|---|---|
| invalid config, frequency, limits, or target point | yes |
| rasterio unavailable for the selected local adapter | yes |
| DEM/DSM metadata mismatch | yes |
| dataset CRS not EPSG:5179 | yes |
| unsupported rotated/sheared transform | yes |
| target outside raster extent | yes |
| target DEM/DSM NoData or non-finite | yes |
| target DSM above target flight MSL | yes |
| session creation/closure failure | yes |
| unexpected non-domain implementation exception | yes |
| candidate-count or sample-budget guard exceeded | yes |

Candidate-level conditions:

| Condition | Candidate state |
|---|---|
| horizontal or authoritative 3D radius exceeded | `outside_operating_radius` |
| candidate outside raster | `outside_raster_extent` |
| candidate DEM/DSM NoData or non-finite | `terrain_nodata` |
| candidate DSM above launch antenna MSL | `launch_surface_obstructed` |
| center equals target when explicitly included | `coincident_with_target` |
| profile sample outside raster or NoData | `profile_unavailable` |
| candidate-specific LOS/Fresnel/scoring/classification domain error | `analysis_invalid` |
| source-zone provider unavailable | core state unchanged; source zone `unavailable` plus warning |

Domain exceptions must be chained into the fatal error or recorded reason. Unexpected programming errors must not be silently converted into candidate exclusions.

## Performance Contract

Task 035B must satisfy:

```text
metadata validation: once per analysis session
DEM open count: one per analysis session
DSM open count: one per analysis session
source-zone raster open count: one batch session when requested
candidate order: deterministic
full-raster preload: not required
```

Default guardrails:

```text
max_candidate_count = 2,500
max_profile_samples_per_candidate = 512
max_total_profile_samples = 250,000
```

The pipeline may perform window reads per sample while reusing open handles. Batch/window optimization may follow later, but correctness checks, NoData handling, and validation may not be skipped for speed.

First optional local smoke boundary:

```text
operating_radius_m <= 900
candidate_spacing_m >= 180
profile_sample_spacing_m >= 90
include_center = false
include_out_of_radius = true
expected square-window candidate count <= 121
expected profile samples per valid candidate <= 11
```

The smoke is a guardrail, not a permanent product limit.

## Task 035B Test Matrix

### CI pure tests

```text
config validation and guard estimates
projected target and deterministic candidate order
flat in-memory terrain
ridge LOS blocking
DSM building/canopy obstacle
frequency sensitivity
2D versus authoritative 3D radius boundary
raster lower-inclusive / upper-exclusive edges
candidate outside raster exclusion
target outside raster fatal
candidate NoData exclusion
target NoData fatal
profile interior NoData exclusion
launch-surface obstruction
occupied-endpoint equality policy
strict LOS interior cap
existing score/color exact regression
dominant diagnostic projection
coincident-center exclusion
source-zone omitted / available / unavailable
source-zone batch order and length checks
actual candidate geometry and no placeholder coordinates
record/feature order parity
zero-valid partial result warning
input immutability
no file creation
existing synthetic scenario and map-output regression
preview/report/CLI regression
```

### Optional local integration

```text
rasterio available
user-provided DEM/DSM paths
small bounded 900m / 180m / 90m configuration
one analysis session
no committed result artifact
aggregate summary only in public handoff
```

### Manual QGIS review

```text
candidate point overlay against EPSG:5179 raster
sampled cell spot checks
candidate-to-target profile spot checks
color distribution sanity review
source-zone boundary spot checks when provider is enabled
```

Task 035A does not execute these checks.

## Compatibility and Invariants

Unchanged:

```text
dsm_fresnel_score == average_fresnel_score
shielding_stability_score = dsm_los_score * 0.40 + dsm_fresnel_score * 0.60
overall_score = shielding_stability_score * 0.80 + distance_score * 0.20
strict LOS cap
color thresholds
candidate score/ranking behavior
route cost
waypoint cost
preview/report/CLI contracts
SyntheticCandidateRecord
build_candidate_cell_map_features synthetic placeholder regression
```

The occupied-endpoint policy is confined to the new real-terrain pipeline and does not alter the standalone LOS function default contract.

Diagnostics remain offline terrain/surface support proxies. They are not a full link budget, RSSI, SINR, packet-loss, communication-success, reconnaissance-success, or flight-feasibility prediction.

## Task 035B Candidate Source Scope

Expected new or modified source:

```text
src/uav_rf_terrain/real_terrain_candidate_analysis.py
src/uav_rf_terrain/geotiff_terrain_data.py
src/uav_rf_terrain/__init__.py
examples/local_real_terrain_candidate_analysis_smoke.py
```

Expected tests:

```text
tests/test_real_terrain_candidate_analysis.py
tests/test_geotiff_terrain_analysis_session.py
existing grid/profile/LOS/Fresnel/scoring/classification/source-zone/map-output regression tests
```

Protected unless a concrete blocker is demonstrated:

```text
src/uav_rf_terrain/scenario_outputs.py
src/uav_rf_terrain/map_outputs.py
src/uav_rf_terrain/candidate_display_outputs.py
src/uav_rf_terrain/candidate_display_preview.py
src/uav_rf_terrain/preview_report.py
src/uav_rf_terrain/preview_cli.py
src/uav_rf_terrain/routing.py
src/uav_rf_terrain/waypoints.py
```

## Non-Goals

Task 035A and Task 035B do not authorize:

- GeoTIFF or GIS data commits;
- `METADATA_MAP` contents in Git;
- generated JSON, table, report, raster, image, PDF, CSV, archive, or QGIS project commits;
- map rendering or UI implementation;
- route/waypoint/minimum-altitude integration;
- credential or private path exposure;
- external-device, autopilot, vehicle-control, or flight-control output.
