# Task 035A Real-Terrain Launch-Area Analysis Pipeline Boundary

## Purpose

Provide the implementation handoff for Task 035B after auditing the current real-terrain, synthetic, source-zone, and map-output contracts.

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
Draft PR: pending creation after documentation commit
PR title: docs: define real-terrain launch-area pipeline boundary
```

The Draft PR must include `Closes #96` and remain Draft until explicit user approval.

## Agent Selection

```text
Cloud Execution Agent
```

Reason: GitHub source/test/document audit and contract documentation only. No rasterio/GDAL/QGIS execution or local DEM/DSM path is required.

## Files Audited

Governance and roadmap:

```text
AGENTS.md
CLAUDE.md
README.md
docs/master-plan.md
docs/research/research-index.md
docs/data/terrain-data-policy.md
docs/architecture/mgrs-external-io-policy.md
.github/workflows/ci.yml
```

Historical real-terrain/source records:

```text
docs/handoff/task-018b-local-dem-dsm-smoke-qgis-checkpoint.md
docs/handoff/task-018c-manual-qgis-overlay-verification.md
docs/handoff/task-018d-qgis-overlay-followup.md
docs/handoff/task-018e-mcee-wms-landcover-gap-fill.md
docs/handoff/task-018f-mixed-source-boundary-quantification.md
docs/handoff/task-020b-local-source-zone-raster-classifier.md
```

Runtime source:

```text
coordinates.py
grid.py
terrain_data.py
geotiff_terrain_data.py
profile.py
los.py
fresnel.py
fresnel_diagnostics.py
scoring.py
classification.py
source_zones.py
source_zone_raster.py
candidate_source_zones.py
scenario_outputs.py
map_outputs.py
candidate_display_outputs.py
candidate_display_preview.py
examples/local_geotiff_adapter_smoke.py
```

Relevant current tests were inspected for candidate-grid order, profiles, GeoTIFF alignment/NoData, LOS, scoring, map outputs, source-zone assignment, and existing synthetic/output regressions.

## Current Audit Summary

### GeoTIFF adapter

- validates aligned DEM/DSM metadata and values;
- lazy-loads rasterio;
- keeps runtime paths out of public metadata;
- currently revalidates/reopens rasters for value calls;
- requires a session path before candidate-grid scale use.

### Profile

- includes endpoints;
- uses deterministic straight-line sampling;
- current adapter path performs repeated DEM/DSM/delta calls;
- generic metadata rounding is not the authoritative real-GeoTIFF point-to-cell rule.

### Grid

- deterministic `ix` then `iy` order;
- stable cell IDs;
- current 3D distance is pre-terrain and must be recomputed after endpoint altitudes are known.

### LOS/Fresnel

- LOS uses `DSM >= line` and currently includes endpoints;
- strict LOS cap remains required;
- real pipeline needs an occupied-endpoint policy without changing standalone LOS defaults;
- Fresnel average and dominant-obstacle diagnostics are reusable unchanged.

### Scoring/classification

- existing weights, strict cap, and thresholds are reused exactly;
- invalid terrain states are exclusions, not zero scores.

### Source zone

- local raster classifier already has an efficient batch open session;
- existing generic assignment is per-point and fatal on provider error;
- first real pipeline uses an optional batch provider and explicit unavailable states.

### Map output

- current `CandidateCellMapFeature` can hold projected geometry but its builder accepts synthetic records and creates placeholder x/y;
- Task 035B introduces a separate production-neutral record and feature in the new module;
- existing synthetic builder remains unchanged.

## Selected Pipeline Boundary

```text
EPSG:5179 target LocalPoint
+ frozen analysis config
+ TerrainDataAdapter
→ one terrain analysis session
→ deterministic candidate grid
→ actual DEM/DSM candidate analysis
→ DSM LOS/Fresnel/diagnostics
→ existing score/color
→ optional source-zone batch attachment
→ candidate records
→ actual projected rendering-independent candidate features
→ summary and warnings
```

Excluded:

```text
MGRS wrapper
rendered map
click selection
route search
route alternatives
waypoints
minimum altitude
UI
Android/TMMR
field RF validation
```

## Task 035B API

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

The architecture document contains the exact configuration, record, feature, result, source-zone, session, and error fields.

## Key Implementation Rules

### Coordinates

- Task 035B input is projected EPSG:5179 only.
- `target_point.z_m` must be zero; altitude is separate.
- real GeoTIFF point sampling uses the open affine transform, not metadata rounding;
- map feature x/y is internal renderer geometry;
- MGRS remains future user-facing wrapper work.

### Altitudes

```text
launch ground = candidate DEM
launch antenna = candidate DEM + launch antenna AGL
target flight = target DEM + allowed AGL
DSM = obstruction surface
```

Default launch antenna AGL is 0.0. A candidate with DSM above the antenna is excluded. The target DSM above target flight altitude is fatal.

### Endpoint LOS

Preserve `analyze_dsm_los(...)` default behavior and tests. The new pipeline must apply a narrow occupied-endpoint normalization so only interior blocked samples trigger the strict cap after endpoint surface prechecks.

### Radius

- horizontal distance is an early precheck;
- authoritative 3D distance uses launch antenna MSL and target flight MSL;
- grid `CandidateCell.distance_3d_m` is not the final real-terrain distance.

### States

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

Only `valid_scored` has a score and non-excluded color.

### Partial results

Zero valid scores are allowed as a deterministic result with warning. Do not discard exclusion evidence.

### Source zone

- optional one-batch provider;
- omitted: `not_requested`;
- provider/raster failure: `unavailable` plus warning;
- bounds/NoData candidate: `not_applicable`;
- never default unavailable to ESA;
- never alter score or color.

### Performance

```text
one metadata validation per session
one DEM open per session
one DSM open per session
no full nationwide raster preload required
no candidate/sample reopen loop
```

Default guards:

```text
2,500 candidates
512 samples per candidate
250,000 total profile samples
```

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

Run existing grid/profile/LOS/Fresnel/scoring/classification/source-zone/map-output/synthetic/output regressions.

## Task 035B Test Matrix

```text
config and performance guards
projected coordinate and affine cell mapping
candidate deterministic order and IDs
flat, ridge, building/canopy
frequency sensitivity
2D vs 3D radius
lower-inclusive / upper-exclusive raster bounds
candidate NoData exclusion
target NoData fatal
profile NoData exclusion
launch-surface exclusion
target surface fatal
occupied endpoint equality
interior strict LOS cap
exact existing score/color regression
dominant diagnostics
source-zone not requested/available/unavailable
batch provider order/length
actual geometry and no placeholder values
record/feature parity
zero-valid warning
input immutability
session open counts
no file creation
synthetic/preview/report/CLI regressions
```

## Optional Local GIS Smoke

Local Execution Agent only, after implementation and user data confirmation:

```text
radius <= 900m
candidate spacing >= 180m
profile spacing >= 90m
include center = false
include out of radius = true
candidate square <= 121
profile samples <= 11 per valid candidate
```

Validate:

```text
rasterio available
DEM/DSM metadata aligned
aggregate state/color counts
single-session open behavior
no committed output
```

Optional QGIS manual review:

```text
candidate point overlay
sampled cell spot check
profile spot check
color distribution sanity check
source-zone boundary spot check
```

Task 035A did not run these commands or access these files.

## Protected Paths and Behavior

Task 035A changes no source, tests, workflow, dependency, lock file, GIS data, or generated output.

Task 035B should not modify the following without a demonstrated blocker and scope review:

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

Unchanged behavior:

```text
Fresnel average meaning
score formulas
strict LOS cap
color thresholds
candidate ranking
route cost
waypoint cost
preview/report/CLI contracts
synthetic scenario and placeholder builder regression
```

## Local Execution Claims

The Cloud Execution Agent did not execute:

```text
compileall
pytest
Ruff
mypy
GeoTIFF or candidate analysis
rasterio
GDAL
QGIS
map rendering
```

GitHub Actions evidence will be added after Draft PR creation and final-head completion.

## Limitations

- This handoff is a code/document contract, not implementation evidence.
- Historical DSM is a landcover-derived proxy and source-boundary sensitivity remains material.
- No terrain accuracy, RF link, communication, reconnaissance, or flight outcome is validated.
- No actual coordinate or private path is recorded.

## Public Repository Sensitivity Check

No DEM/DSM, landcover raster, `METADATA_MAP` content, generated artifact, credential, private path, operational command, device command, autopilot command, or flight-control output is added.
