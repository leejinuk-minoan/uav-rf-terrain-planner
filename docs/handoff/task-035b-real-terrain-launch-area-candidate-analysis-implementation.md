# Task 035B Real-Terrain Launch-Area Candidate Analysis Implementation

## Current Task

Task 035B implements the first session-backed real-terrain candidate-analysis engine.
The implementation ends with immutable candidate records, projected renderer-input
features, deterministic summaries, and warnings. It does not render a map, accept
MGRS, search routes, create waypoints, or add a UI.

## Public API

`uav_rf_terrain.real_terrain_candidate_analysis` provides:

- `RealTerrainLaunchAreaConfig`;
- `analyze_real_terrain_launch_area(...)`;
- `CandidateAnalysisRecord` and `CandidateAnalysisMapFeature`;
- explicit candidate and source-zone availability states;
- immutable result and summary records.

The engine receives an internal EPSG:5179 `LocalPoint` developer/runtime input.
The user-facing MGRS boundary remains a later wrapper task.

## Session and Candidate Behavior

- `LocalGeoTiffTerrainDataAdapter.open_analysis_session()` opens one DEM and one DSM
  handle, validates paired metadata once, and reuses the handles for point and profile
  reads.
- The GeoTIFF session supports only north-up, unrotated transforms and uses
  `dataset.index(x, y)` plus row/column range checks for point sampling.
- The generic compatibility session preserves pure in-memory adapter coverage without
  requiring rasterio in CI.
- Candidate records preserve deterministic existing grid order and distinguish valid
  scoring from radius, extent, NoData, surface, coincident, profile, and analysis
  exclusions.
- Pipeline-only occupied-endpoint handling retains standalone LOS behavior while
  applying the strict LOS cap to interior blockers.
- Existing Fresnel calculations, score weights, color thresholds, synthetic outputs,
  preview/report/CLI behavior, route behavior, and waypoint behavior remain unchanged.

## Source-Zone Boundary

The optional batch provider receives eligible requested candidate points in filtered
candidate order. Provider omission, success, and failure map to the approved
availability states without changing core score, color, candidate order, or candidate
state. A failure creates one deterministic warning.

## Verification

Local verification on the implementation branch:

```text
focused candidate/session tests: passed
existing terrain/profile/LOS/Fresnel/scoring/classification/source-zone/map regressions: passed
full pytest: 782 passed
ruff: passed
mypy: passed
```

`rasterio` and the expected local DEM/DSM paths were present, but no previously
approved smoke target was available. The optional real-data smoke was skipped rather
than creating or publishing a coordinate.

## Repository Safety

No DEM, DSM, landcover, `METADATA_MAP` content, QGIS project, generated result,
private path, credential, or device/flight-control content is part of this task.

## Follow-Up

1. GPT Master review of the Draft PR and public contract.
2. A separately approved bounded local smoke may use an existing approved target.
3. MGRS wrapper, rendered map, route, waypoint, and UI work remain separate tasks.
