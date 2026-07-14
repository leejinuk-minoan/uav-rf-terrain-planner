# Task 035A Real-Terrain Launch-Area Analysis Pipeline Boundary

## Purpose

Provide the reviewed implementation handoff for Task 035B after auditing the current GeoTIFF, terrain-profile, LOS/Fresnel, scoring/classification, source-zone, synthetic-output, and map-output contracts.

Task 035A is documentation/code-contract audit work only. It does not implement or execute the real-terrain pipeline.

## Start Gate

Verified before branch creation:

```text
repository: leejinuk-minoan/uav-rf-terrain-planner
PR #95: merged to main
base main / merge commit: 66f2eb7982bea47598b13afd7fffe157fcdbfcb6
Issue #94: closed / completed
Issue #96: open
Task 034D implementation: present on main
EXP-20260714-050: present on main
open PRs before Task 035A: none
related open real-terrain pipeline issue: #96
```

## Branch and Draft PR

```text
branch: agent/task-035a-real-terrain-launch-area-pipeline-contract
Draft PR: #97
PR title: docs: define real-terrain launch-area pipeline boundary
PR state: open / draft / unmerged
```

The Draft PR includes `Closes #96` and remains Draft until explicit user approval.

## Agent Selection

```text
Cloud Execution Agent
```

Reason: the task requires GitHub source/test/document inspection, code-contract design, documentation, Draft PR creation, and CI observation. It does not require a local GIS environment.

## Current Audit Summary

### GeoTIFF adapter

The current `LocalGeoTiffTerrainDataAdapter`:

- validates DEM/DSM CRS, bounds, dimensions, resolution, NoData, and finite cell values;
- imports rasterio lazily;
- excludes private paths from public metadata;
- currently revalidates and reopens rasters for individual value calls;
- is suitable for a small smoke boundary but not a candidate/profile loop without a session path.

### Terrain profile

The current adapter profile:

- includes start and end samples;
- uses deterministic straight-line fractions;
- can repeat sampled cells when spacing is finer than raster resolution;
- currently performs separate DEM, DSM, and surface-delta calls per sample;
- uses a generic metadata-rounding helper that must not be the authoritative real-GeoTIFF sampler.

### Candidate grid

The grid contract is reusable for:

```text
deterministic ix then iy order
stable candidate IDs
square window generation
horizontal precheck
```

Its current `distance_3d_m` is not authoritative for real terrain because candidate and target MSL values have not yet been sampled.

### LOS and Fresnel

- standalone LOS treats `DSM >= LOS line` as blocked and includes endpoints;
- strict LOS cap remains unchanged;
- Task 035B needs a pipeline-only occupied-endpoint policy after endpoint surface validation;
- standalone LOS behavior and tests remain unchanged;
- Fresnel average, dominant-obstacle selection, and diagnostic projection are reused unchanged.

### Scoring and classification

The existing score formulas, strict LOS cap, and color thresholds remain authoritative. Raster/data failures become exclusions and are not represented as score zero.

### Source zone

- the local raster classifier already supports batch sampling with one open session;
- the generic assignment scaffold is per-point and treats provider failure as fatal;
- Task 035B uses an optional batch provider and explicit availability states;
- unavailable source-zone data never defaults to ESA-derived and never changes score or color.

### Synthetic and map output

`SyntheticCandidateRecord` remains synthetic. The current candidate map builder creates placeholder geometry and is retained only for synthetic regression.

Task 035B introduces a production-neutral record and actual projected rendering-independent feature rather than modifying the synthetic record or placeholder builder.

## Selected Pipeline Boundary

```text
EPSG:5179 target LocalPoint
+ frozen analysis configuration
+ TerrainDataAdapter
→ one terrain analysis session
→ deterministic candidate grid
→ actual DEM/DSM candidate analysis
→ DSM LOS/Fresnel/diagnostics
→ existing score/color
→ optional source-zone batch attachment
→ production-neutral candidate records
→ actual projected rendering-independent candidate features
→ deterministic summary and warnings
```

Excluded from Task 035B:

```text
MGRS conversion wrapper
rendered map
map click selection
route search and alternatives
waypoints
minimum-required-altitude integration
Streamlit/Folium/MapLibre UI
Android/TMMR
field RF validation
```

## Task 035B Public API

Create:

```text
src/uav_rf_terrain/real_terrain_candidate_analysis.py
```

Function:

```python
analyze_real_terrain_launch_area(
    adapter: TerrainDataAdapter,
    config: RealTerrainLaunchAreaConfig,
    *,
    source_zone_provider: SourceZoneBatchProvider | None = None,
) -> RealTerrainLaunchAreaResult
```

The function is deterministic, does not mutate its inputs, writes no file, and renders no map.

## Configuration Contract

Required frozen configuration fields:

```text
scenario_name
target_point: LocalPoint
operating_radius_m
candidate_spacing_m
allowed_agl_m
frequency_hz
profile_sample_spacing_m = None
launch_antenna_height_agl_m = 0.0
include_center = false
include_out_of_radius = true
max_candidate_count = 2500
max_profile_samples_per_candidate = 512
max_total_profile_samples = 250000
```

All numeric values must be finite. Distances, spacing, AGL, frequency, and limits must be positive except launch antenna AGL, which may be zero. `target_point.z_m` must be zero because altitude is configured separately.

## Coordinate Contract

Task 035B input:

```text
EPSG:5179 LocalPoint
```

MGRS remains the default project user-facing coordinate policy, but conversion is deferred to a wrapper task.

Real GeoTIFF sampling rules:

```text
supported transform: a > 0, e < 0, b == 0, d == 0
point-to-cell authority: dataset.index(x, y)
in-bounds authority: 0 <= row < height and 0 <= col < width
directional precheck only: left <= x < right and bottom < y <= top
requested candidate point retained as feature geometry
sampled cell center retained as internal diagnostic geometry
```

Unsupported transform signs, rotation, or shear are fatal `RealTerrainLaunchAreaAnalysisError` conditions. The directional precheck is secondary; the index result and row/column range determine whether a point is sampleable. The exact policy is left inclusive, right exclusive, top inclusive, and bottom exclusive.

Task 035B feature coordinate fields:

```text
x_m/y_m = actual projected renderer geometry
geometry_crs = EPSG:5179
candidate_cell_mgrs = None
coordinate_display_state = projected_only
```

Projected and raster coordinates are internal, not default user-facing coordinate fields.

## Altitude and Distance Contract

```text
launch_ground_msl = candidate DEM MSL
launch_surface_msl = candidate DSM MSL
launch_antenna_msl = launch_ground_msl + launch_antenna_height_agl_m

target_ground_msl = target DEM MSL
target_surface_msl = target DSM MSL
target_flight_msl = target_ground_msl + allowed_agl_m
```

Policy:

- DEM is the AGL reference surface;
- DSM is the obstruction surface;
- candidate DSM above launch antenna MSL produces `launch_surface_obstructed`;
- target DSM above target flight MSL is fatal;
- equality at an occupied endpoint is permitted;
- only interior blocked samples trigger the strict LOS cap;
- authoritative 3D distance uses launch-antenna and target-flight MSL values.

## Candidate States

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

Only `valid_scored` contains a `CandidateScore` and non-excluded color. Other states use `ColorClass.EXCLUDED`, `None` score values, and explicit reasons.

A valid LOS-blocked candidate remains `valid_scored`; it receives the existing LOS score zero, strict shielding cap, and existing color classification.

## Fatal versus Candidate-Level Failure

Fatal:

```text
invalid configuration, target, frequency, or limits
rasterio unavailable for a selected local adapter
DEM/DSM metadata mismatch
non-EPSG:5179 dataset
transform other than a > 0, e < 0, b == 0, d == 0
target outside raster
target NoData or non-finite
target DSM above target flight MSL
analysis-session failure
candidate/sample guard exceeded
unexpected non-domain implementation exception
```

Candidate-level:

```text
2D or authoritative 3D radius exceeded
candidate outside raster
candidate NoData or non-finite
candidate DSM above launch antenna
coincident target when center explicitly included
profile outside raster or profile NoData
candidate-specific LOS/Fresnel/scoring/classification domain error
```

Source-zone provider failure does not change the core candidate state.

Partial results are permitted, including zero valid candidates. Zero-valid output includes:

```text
no valid scored candidates were produced
```

## Source-Zone Contract

Availability states:

```text
available
not_requested
unavailable
not_applicable
```

Policy:

- provider is optional;
- provider eligibility requires `sampled_cell_center is not None` and a state other than `outside_operating_radius`, `outside_raster_extent`, or `terrain_nodata`;
- eligible projected points are sent in one batch in filtered input candidate order;
- count/order mismatch is invalid provider output;
- provider exception or missing landcover leaves eligible core scores and candidate states unchanged, marks eligible source zones unavailable, and adds one deterministic warning;
- unavailable is never converted to ESA-derived;
- source zone does not change scoring, color, ordering, or candidate state.

| Candidate state | Provider batch | Omitted | Success | Failure |
|---|---|---|---|---|
| `valid_scored` | included when sampled cell exists | `not_requested` | `available` | `unavailable` |
| `launch_surface_obstructed` | included when sampled cell exists | `not_requested` | `available` | `unavailable` |
| `coincident_with_target` | included when sampled cell exists | `not_requested` | `available` | `unavailable` |
| `profile_unavailable` | included when sampled cell exists | `not_requested` | `available` | `unavailable` |
| `analysis_invalid` | included when sampled cell exists | `not_requested` | `available` | `unavailable` |
| `outside_operating_radius` | excluded | `not_applicable` | `not_applicable` | `not_applicable` |
| `outside_raster_extent` | excluded | `not_applicable` | `not_applicable` | `not_applicable` |
| `terrain_nodata` | excluded | `not_applicable` | `not_applicable` | `not_applicable` |

## Performance Contract

Required first implementation behavior:

```text
metadata validation once per analysis session
DEM opened once per analysis session
DSM opened once per analysis session
profile reads reuse the open handles
optional source-zone rasters use one batch session
full nationwide raster preload not required
```

Default limits:

```text
2500 candidates
512 samples per candidate
250000 total profile samples
```

First optional local smoke boundary:

```text
operating radius <= 900m
candidate spacing >= 180m
profile spacing >= 90m
include center = false
include out of radius = true
candidate square <= 121
profile samples <= 11 per valid candidate
```

## Result Contract

Return frozen:

```text
CandidateAnalysisRecord
CandidateAnalysisMapFeature
RealTerrainLaunchAreaSummary
RealTerrainLaunchAreaResult
```

Records and features have the same length and order. State, color, and source-zone count summaries use deterministic enum declaration order. Full profile/LOS/Fresnel sample arrays are not retained in every result record.

## Task 035B Candidate Files

Expected source:

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
```

Run existing grid, profile, LOS, Fresnel, scoring, classification, source-zone, map-output, synthetic, preview, report, and CLI regressions.

## Test Matrix

```text
configuration and performance guards
EPSG:5179 target validation
affine point-to-cell mapping
candidate order and IDs
flat, ridge, building/canopy scenarios
frequency sensitivity
2D versus 3D radius
supported north-up transform (`a > 0`, `e < 0`, `b == 0`, `d == 0`)
left/right/top/bottom exact edges and inside/outside epsilon cases
unsupported transform signs, rotation, or shear fatal
candidate NoData exclusion
target NoData fatal
profile NoData exclusion
launch-surface obstruction
target surface fatal
occupied-endpoint equality
interior strict LOS cap
existing score/color exact regression
dominant-obstacle projection
source-zone membership, order, and count for every candidate state
source-zone omitted/success/failure availability mapping for every candidate state
actual candidate geometry and no placeholder values
record/feature order parity
zero-valid warning
input immutability
session open counts
no file creation
existing synthetic/output regressions
```

## Optional Local GIS Verification

Local Execution Agent only, after Task 035B implementation and user data confirmation:

```text
rasterio availability
user DEM/DSM paths
bounded smoke configuration
aggregate state/color/source-zone summary
one-session open behavior
no committed generated output
```

Optional manual QGIS checks:

```text
candidate point overlay
sampled-cell spot checks
candidate-to-target profile spot checks
color distribution sanity review
source-zone boundary spot checks
```

Task 035A did not execute any of these checks.

## Protected Paths and Invariants

Task 035A changes no source, tests, workflow, dependency, lock file, GIS data, or generated output.

Task 035B should not modify without a demonstrated blocker:

```text
scenario_outputs.py
map_outputs.py
candidate_display_outputs.py
candidate_display_preview.py
preview_report.py
preview_cli.py
routing.py
waypoints.py
```

Unchanged:

```text
dsm_fresnel_score == average_fresnel_score
DSM LOS 0.40 + DSM Fresnel 0.60
shielding 0.80 + distance 0.20
strict LOS cap
color thresholds
candidate ranking
route cost
waypoint cost
preview/report/CLI contracts
synthetic scenario and placeholder-builder regression
```

## GitHub Actions Evidence

Initial Draft PR documentation head:

```text
run: CI #834
head: aab2ec9a572af4f9f23a0786c700984630ed392b
status: completed
conclusion: success
steps: install, syntax check, pytest, Ruff, mypy successful
```

The final-head CI result is recorded in the Draft PR body and Task 035A completion report after the final documentation commit.

## Local Execution Claims

The Cloud Execution Agent did not execute:

```text
compileall
pytest
Ruff
mypy
GeoTIFF candidate analysis
rasterio
GDAL
QGIS
map rendering
```

## Limitations

- This handoff is a code/document contract, not implementation evidence.
- Historical DSM is a landcover-derived proxy and mixed-source sensitivity remains material.
- No terrain accuracy, RF link, communication, reconnaissance, or flight outcome is validated.
- No actual candidate coordinate or private path is recorded.

## Public Repository Sensitivity Check

No DEM/DSM, landcover raster, `METADATA_MAP` content, generated artifact, credential, private path, operational command, device command, autopilot command, or flight-control output is added.
